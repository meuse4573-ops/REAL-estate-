"""
PDF Document Parser using pdfplumber.
Extracts text from PDF files with layout preservation.
"""
import pdfplumber
from typing import Optional, Dict, Any
import os


class PDFParser:
    """PDF text extraction using pdfplumber."""
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract all text from a PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[Page {page_num}]\n{page_text}")
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def extract_tables(file_path: str) -> list:
        """
        Extract tables from PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of extracted tables
        """
        tables = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
        
        return tables
    
    @staticmethod
    def get_metadata(file_path: str) -> Dict[str, Any]:
        """
        Get PDF metadata.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Metadata dictionary
        """
        with pdfplumber.open(file_path) as pdf:
            return {
                "page_count": len(pdf.pages),
                "metadata": pdf.metadata or {},
                "first_page_width": pdf.pages[0].width if pdf.pages else 0,
                "first_page_height": pdf.pages[0].height if pdf.pages else 0,
            }
    
    @staticmethod
    def is_scanned(file_path: str) -> bool:
        """
        Check if PDF is scanned (image-based) vs text-based.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if scanned PDF
        """
        with pdfplumber.open(file_path) as pdf:
            first_page_text = pdf.pages[0].extract_text() if pdf.pages else ""
            return len(first_page_text.strip()) < 50