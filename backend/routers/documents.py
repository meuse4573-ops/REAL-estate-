"""
Document upload and extraction endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
from datetime import datetime

from core.database import Database
from core.dependencies import get_current_agent, Agent
from services.document_intelligence.extractor import trec_extractor
from services.document_intelligence.validator import trec_validator


router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentResponse(BaseModel):
    id: str
    deal_id: Optional[str]
    file_name: str
    file_path: str
    type: Optional[str]
    extraction_confidence: Optional[float]
    is_signed: bool
    uploaded_at: str


class ExtractionResult(BaseModel):
    document_id: str
    property_address: Optional[str]
    purchase_price: Optional[float]
    earnest_money: Optional[float]
    option_fee: Optional[float]
    option_period_days: Optional[int]
    acceptance_date: Optional[str]
    closing_date: Optional[str]
    buyers: List[dict]
    sellers: List[dict]
    deadlines: List[dict]
    validation: dict
    confidence: float
    warnings: List[str]


@router.post("/upload", response_model=dict)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    deal_id: Optional[str] = None,
    agent: Agent = Depends(get_current_agent)
):
    """
    Upload a PDF document (TREC contract) for extraction.
    
    - Saves file to uploads directory
    - Triggers background extraction with GLM 5.1
    - Returns document ID for polling extraction status
    
    Args:
        file: PDF file to upload
        deal_id: Optional deal ID to associate with
        
    Returns:
        Document ID and upload status
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    upload_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    doc_id = str(uuid.uuid4())
    
    await Database.execute_query(
        """
        INSERT INTO documents (id, deal_id, file_name, file_path, type, uploaded_at)
        VALUES ($1, $2, $3, $4, $5, NOW())
        """,
        doc_id, deal_id, file.filename, file_path, "purchase_agreement"
    )
    
    background_tasks.add_task(process_document_extraction, doc_id, file_path, agent.id)
    
    return {
        "document_id": doc_id,
        "file_name": file.filename,
        "status": "uploaded",
        "message": "Document uploaded. Extraction in progress..."
    }


async def process_document_extraction(doc_id: str, file_path: str, agent_id: str):
    """Background task to extract data from document."""
    try:
        extraction_result = await trec_extractor.extract_with_confidence(file_path)
        extraction = extraction_result["extraction"]
        
        validation = trec_validator.validate(extraction)
        
        await Database.execute_query(
            """
            UPDATE documents 
            SET extracted_text = $1, 
                extraction_confidence = $2,
                processed_at = NOW(),
                type = $3
            WHERE id = $4
            """,
            str(extraction), extraction_result["confidence"], extraction.get("form_type", "purchase_agreement"), doc_id
        )
        
        deal_id = await Database.fetch_val(
            "SELECT deal_id FROM documents WHERE id = $1", doc_id
        )
        
        if deal_id and extraction.get("property_address"):
            await Database.execute_query(
                """
                UPDATE deals 
                SET address = $1, 
                    purchase_price = COALESCE($2, purchase_price),
                    earnest_money = COALESCE($3, earnest_money),
                    option_fee = COALESCE($4, option_fee),
                    option_period_days = COALESCE($5, option_period_days),
                    acceptance_date = $6,
                    closing_date = $7,
                    updated_at = NOW()
                WHERE id = $8
                """,
                extraction.get("property_address"),
                extraction.get("purchase_price"),
                extraction.get("earnest_money"),
                extraction.get("option_fee"),
                extraction.get("option_period_days"),
                extraction.get("acceptance_date"),
                extraction.get("closing_date"),
                deal_id
            )
            
            for buyer in extraction.get("buyers", []):
                await Database.execute_query(
                    """
                    INSERT INTO parties (deal_id, role, name, email, phone)
                    VALUES ($1, 'buyer', $2, $3, $4)
                    """,
                    deal_id, buyer.get("name"), buyer.get("email"), buyer.get("phone")
                )
            
            for seller in extraction.get("sellers", []):
                await Database.execute_query(
                    """
                    INSERT INTO parties (deal_id, role, name, email, phone)
                    VALUES ($1, 'seller', $2, $3, $4)
                    """,
                    deal_id, seller.get("name"), seller.get("email"), seller.get("phone")
                )
            
            for deadline in extraction.get("deadlines", []):
                await Database.execute_query(
                    """
                    INSERT INTO deadlines (deal_id, type, deadline_date, extracted_from)
                    VALUES ($1, $2, $3, $4)
                    """,
                    deal_id, deadline.get("type"), deadline.get("date"), "contract_extraction"
                )
        
    except Exception as e:
        await Database.execute_query(
            "UPDATE documents SET extracted_text = $1 WHERE id = $2",
            f"Error: {str(e)}", doc_id
        )


@router.get("/{document_id}/extract")
async def get_extraction_result(document_id: str, agent: Agent = Depends(get_current_agent)):
    """
    Get extraction results for a document.
    
    Args:
        document_id: Document ID from upload
        
    Returns:
        Full extraction results with validation
    """
    doc = await Database.fetch_one(
        "SELECT * FROM documents WHERE id = $1", document_id
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not doc.get("extracted_text"):
        return {"status": "processing", "message": "Extraction in progress"}
    
    import json
    extraction = json.loads(doc["extracted_text"]) if isinstance(doc["extracted_text"], str) else doc["extracted_text"]
    
    validation = trec_validator.validate(extraction)
    
    return {
        "document_id": document_id,
        "status": "completed",
        "extraction": extraction,
        "validation": validation,
        "confidence": doc.get("extraction_confidence"),
        "processed_at": doc.get("processed_at")
    }


@router.get("/deal/{deal_id}")
async def get_deal_documents(deal_id: str, agent: Agent = Depends(get_current_agent)):
    """Get all documents for a deal."""
    docs = await Database.fetch_rows(
        """
        SELECT id, file_name, type, extraction_confidence, uploaded_at, processed_at
        FROM documents 
        WHERE deal_id = $1
        ORDER BY uploaded_at DESC
        """,
        deal_id
    )
    
    return {"documents": [dict(d) for d in docs]}