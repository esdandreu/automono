"""
Invoice domain model.

Unified model containing both metadata and file content for an invoice.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, ClassVar


@dataclass
class Invoice:
    """Unified invoice model containing both metadata and file content."""
    
    # Metadata fields
    invoice_date: datetime  # Extracted from invoice document
    concept: str  # Provider-specific parameter (e.g., "Electricity", "Internet", "Water")
    type: str  # Provider-specific parameter (e.g., "Monthly Bill", "Quarterly Bill")
    cost_euros: Decimal  # Extracted from invoice document
    iva_euros: Decimal  # Extracted from invoice document (VAT amount)
    deductible_percentage: float  # Provider-specific parameter (e.g., 0.0, 0.5, 1.0)
    file_name: str
    
    # File fields
    content: bytes
    content_type: str
    size: int
    hash_md5: str
    hash_sha256: str
    
    def __post_init__(self):
        """Validate the invoice after initialization."""
        # Validate metadata fields
        if self.deductible_percentage < 0.0 or self.deductible_percentage > 1.0:
            raise ValueError("Deductible percentage must be between 0.0 and 1.0")
        
        if self.cost_euros < 0:
            raise ValueError("Cost amount cannot be negative")
        
        if self.iva_euros < 0:
            raise ValueError("IVA amount cannot be negative")
        
        if not self.concept.strip():
            raise ValueError("Concept cannot be empty")
        
        if not self.type.strip():
            raise ValueError("Type cannot be empty")
        
        if not self.file_name.strip():
            raise ValueError("File name cannot be empty")
        
        # Validate file fields
        if len(self.content) == 0:
            raise ValueError("File content cannot be empty")
        
        if self.size != len(self.content):
            raise ValueError("File size must match content length")
        
        if not self.content_type.strip():
            raise ValueError("Content type cannot be empty")
        
        # Verify hashes match content
        if self.hash_md5 != self._calculate_md5():
            raise ValueError("MD5 hash does not match content")
        
        if self.hash_sha256 != self._calculate_sha256():
            raise ValueError("SHA256 hash does not match content")
    
    def _calculate_md5(self) -> str:
        """Calculate MD5 hash of the content."""
        return hashlib.md5(self.content).hexdigest()
    
    def _calculate_sha256(self) -> str:
        """Calculate SHA256 hash of the content."""
        return hashlib.sha256(self.content).hexdigest()
    
    @property
    def total_euros(self) -> Decimal:
        """Calculate the total amount including VAT."""
        return self.cost_euros + self.iva_euros
    
    @property
    def deductible_amount(self) -> Decimal:
        """Calculate the deductible amount based on the percentage."""
        return self.total_euros * Decimal(str(self.deductible_percentage))
    
    @classmethod
    def from_content(
        cls,
        content: bytes,
        file_name: str,
        invoice_date: datetime,
        concept: str,
        type: str,
        cost_euros: Decimal,
        iva_euros: Decimal,
        deductible_percentage: float,
        content_type: str = "application/pdf"
    ) -> "Invoice":
        """Create an Invoice from raw content, calculating hashes automatically."""
        return cls(
            # Metadata fields
            invoice_date=invoice_date,
            concept=concept,
            type=type,
            cost_euros=cost_euros,
            iva_euros=iva_euros,
            deductible_percentage=deductible_percentage,
            file_name=file_name,
            # File fields
            content=content,
            content_type=content_type,
            size=len(content),
            hash_md5=hashlib.md5(content).hexdigest(),
            hash_sha256=hashlib.sha256(content).hexdigest()
        )
