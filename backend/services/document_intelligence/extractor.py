"""
Texas TREC Document Extractor.
Uses GLM 5.1 to extract structured data from real estate contracts.
"""
import json
from typing import Dict, Any, Optional
from .glm_client import glm_client
from .parser import PDFParser
import os


TREC_EXTRACTION_SYSTEM = """You are an expert at reading Texas Real Estate Commission (TREC) contracts.
Extract all relevant information from the contract and return valid JSON.
Focus on Texas TREC-promulgated forms including:
- One to Four Family Residential Contract (TREC 20-14)
- Contract Addendum (TREC 20-15)
- Seller's Disclosure Notice (TREC 20-16)
- Buyer's Inspection Addendum (TREC 20-17)
- Third Party Financing Addendum (TREC 20-18)
- Unimproved Property Contract (TREC 20-19)

Extract ALL dates, amounts, parties, and deadlines. Be thorough."""


TREC_EXTRACTION_PROMPT = """Extract the following information from this TREC contract. 
Return ONLY valid JSON with these exact keys:

1. property_address: Full street address, city, state, zip
2. purchase_price: Numeric amount (or null if not found)
3. earnest_money: Numeric amount
4. option_fee: Numeric amount (for option period)
5. option_period_days: Number of days
6. acceptance_date: Date when contract was accepted (format: YYYY-MM-DD)
7. closing_date: Scheduled closing date (format: YYYY-MM-DD)
8. buyers: Array of {name, email, phone} for each buyer
9. sellers: Array of {name, email, phone} for each seller
10. listing_agent: {name, email, phone, company}
11. selling_agent: {name, email, phone, company}
12. title_company: {name, address, phone}
13. lender: {name, address, phone} (if financing addendum)
14. deadlines: Array of {type, date, description}
    - Types: inspection, financing_contingency, appraisal, title_commitment, closing, possession, option_period
15. special_provisions: Array of any special terms or conditions
16. form_type: Which TREC form this appears to be
17. is_signed: Whether signatures appear to be present

If any field is not found, use null for numeric fields, empty array [] for arrays, empty string "" for strings."""


class TRECExtractor:
    """Extract structured data from Texas TREC contracts using GLM."""
    
    def __init__(self):
        self.parser = PDFParser()
    
    async def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract structured data from a PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Structured extraction results
        """
        is_scanned = self.parser.is_scanned(file_path)
        
        if is_scanned:
            return await self._extract_scanned(file_path)
        else:
            return await self._extract_text_based(file_path)
    
    async def _extract_text_based(self, file_path: str) -> Dict[str, Any]:
        """Extract from text-based PDF using text extraction."""
        text = self.parser.extract_text(file_path)
        metadata = self.parser.get_metadata(file_path)
        
        full_prompt = f"{TREC_EXTRACTION_PROMPT}\n\nContract Content:\n{text[:8000]}"
        
        result = await glm_client.chat_json(
            prompt=full_prompt,
            system=TREC_EXTRACTION_SYSTEM,
            max_tokens=4096
        )
        
        result["is_scanned"] = False
        result["page_count"] = metadata["page_count"]
        
        return result
    
    async def _extract_scanned(self, file_path: str) -> Dict[str, Any]:
        """Extract from scanned PDF using vision model."""
        prompt = TREC_EXTRACTION_PROMPT + "\n\nThis appears to be a scanned document. Please extract all visible information."
        
        result = await glm_client.vision_extract(
            image_path=file_path,
            prompt=prompt,
            max_tokens=4096
        )
        
        parsed = json.loads(result)
        parsed["is_scanned"] = True
        
        return parsed
    
    async def extract_with_confidence(self, file_path: str) -> Dict[str, Any]:
        """
        Extract with confidence score.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extraction with confidence metadata
        """
        result = await self.extract_from_file(file_path)
        
        confidence = self._calculate_confidence(result)
        
        return {
            "extraction": result,
            "confidence": confidence,
            "warnings": self._get_warnings(result)
        }
    
    def _calculate_confidence(self, data: Dict) -> float:
        """Calculate extraction confidence based on data completeness."""
        required_fields = ["property_address", "purchase_price", "buyers", "sellers"]
        filled = sum(1 for f in required_fields if data.get(f))
        return round(filled / len(required_fields), 3)
    
    def _get_warnings(self, data: Dict) -> list:
        """Get warnings about missing or unclear data."""
        warnings = []
        
        if not data.get("purchase_price"):
            warnings.append("Purchase price not found")
        if not data.get("buyers"):
            warnings.append("No buyer information found")
        if not data.get("sellers"):
            warnings.append("No seller information found")
        if not data.get("deadlines"):
            warnings.append("No deadlines extracted")
        if not data.get("closing_date"):
            warnings.append("No closing date found")
        
        return warnings


trec_extractor = TRECExtractor()