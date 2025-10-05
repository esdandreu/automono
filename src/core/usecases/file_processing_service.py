"""
File processing service use case.

Handles PDF validation and metadata extraction from invoice files.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import PyPDF2
import pdfplumber

from ..domain.invoice_file import InvoiceFile
from ..domain.invoice_metadata import InvoiceMetadata
from ...infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class FileProcessingService:
    """Service for processing invoice files and extracting metadata."""
    
    def __init__(self):
        """Initialize the file processing service."""
        self.logger = logger
    
    def extract_metadata_from_pdf(self, invoice_file: InvoiceFile, concept: str, type: str, deductible_percentage: float) -> InvoiceMetadata:
        """
        Extract metadata from a PDF invoice file.
        
        Args:
            invoice_file: The invoice file to process
            concept: Provider-specific concept
            type: Provider-specific type
            deductible_percentage: Provider-specific deductible percentage
            
        Returns:
            Invoice metadata with extracted information
            
        Raises:
            ValueError: If the PDF cannot be processed or metadata cannot be extracted
        """
        try:
            # Extract text from PDF
            text = self._extract_text_from_pdf(invoice_file)
            
            # Extract invoice date
            invoice_date = self._extract_invoice_date(text)
            
            # Extract cost amounts
            cost_euros, iva_euros = self._extract_amounts(text)
            
            # Create metadata
            metadata = InvoiceMetadata(
                invoice_date=invoice_date,
                concept=concept,
                type=type,
                cost_euros=cost_euros,
                iva_euros=iva_euros,
                deductible_percentage=deductible_percentage,
                file_name=invoice_file.file_name
            )
            
            self.logger.info("Successfully extracted metadata from PDF",
                           file_name=invoice_file.file_name,
                           invoice_date=invoice_date.isoformat(),
                           cost_euros=float(cost_euros),
                           iva_euros=float(iva_euros))
            
            return metadata
            
        except Exception as e:
            self.logger.error("Failed to extract metadata from PDF",
                            file_name=invoice_file.file_name,
                            error=str(e))
            raise ValueError(f"Failed to extract metadata from PDF: {e}")
    
    def _extract_text_from_pdf(self, invoice_file: InvoiceFile) -> str:
        """Extract text content from a PDF file."""
        try:
            # Try with pdfplumber first (better for complex layouts)
            with pdfplumber.open(io.BytesIO(invoice_file.content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                if text.strip():
                    return text
            
            # Fallback to PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(invoice_file.content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text
            
        except Exception as e:
            self.logger.error("Failed to extract text from PDF", error=str(e))
            raise ValueError(f"Failed to extract text from PDF: {e}")
    
    def _extract_invoice_date(self, text: str) -> datetime:
        """Extract invoice date from text."""
        # Common date patterns in Spanish invoices
        date_patterns = [
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',  # DD de MMM de YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if len(matches[0]) == 3:
                        day, month, year = matches[0]
                        
                        # Handle Spanish month names
                        if not month.isdigit():
                            month = self._spanish_month_to_number(month)
                        
                        return datetime(int(year), int(month), int(day))
                except (ValueError, TypeError):
                    continue
        
        raise ValueError("Could not extract invoice date from PDF text")
    
    def _extract_amounts(self, text: str) -> tuple[Decimal, Decimal]:
        """Extract cost and IVA amounts from text."""
        # Look for amounts with euro symbols or "EUR"
        amount_patterns = [
            r'(\d+[.,]\d{2})\s*€',  # 123,45 €
            r'€\s*(\d+[.,]\d{2})',  # € 123,45
            r'(\d+[.,]\d{2})\s*EUR',  # 123,45 EUR
            r'(\d+[.,]\d{2})',  # Just numbers with comma/point
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Convert comma to point for decimal parsing
                    amount_str = match.replace(',', '.')
                    amount = Decimal(amount_str)
                    if amount > 0:  # Only positive amounts
                        amounts.append(amount)
                except (InvalidOperation, ValueError):
                    continue
        
        if len(amounts) < 2:
            raise ValueError("Could not extract sufficient amounts from PDF text")
        
        # Sort amounts (usually the largest is the total)
        amounts.sort(reverse=True)
        
        # Assume the largest amount is total, second largest is base cost
        total_amount = amounts[0]
        base_amount = amounts[1] if len(amounts) > 1 else amounts[0]
        
        # Calculate IVA (VAT)
        iva_amount = total_amount - base_amount
        
        return base_amount, iva_amount
    
    def _spanish_month_to_number(self, month_name: str) -> int:
        """Convert Spanish month name to number."""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        month_lower = month_name.lower()
        if month_lower in months:
            return months[month_lower]
        
        raise ValueError(f"Unknown Spanish month: {month_name}")
    
    def validate_pdf_file(self, invoice_file: InvoiceFile) -> bool:
        """Validate that the file is a valid PDF."""
        try:
            # Check if it's a PDF by trying to read it
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(invoice_file.content))
            if len(pdf_reader.pages) == 0:
                return False
            
            # Check file size (should be reasonable)
            if len(invoice_file.content) < 1000:  # Less than 1KB is suspicious
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("PDF validation failed", error=str(e))
            return False


# Import io at the top level
import io
