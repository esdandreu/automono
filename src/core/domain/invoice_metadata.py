"""
Invoice metadata domain model.

Contains the essential information about an invoice including extracted data
from the document and provider-specific parameters.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Final


@dataclass
class InvoiceMetadata:
    """Metadata for an invoice containing both extracted and configured data."""
    
    invoice_date: datetime  # Extracted from invoice document
    concept: str  # Provider-specific parameter (e.g., "Electricity", "Internet", "Water")
    type: str  # Provider-specific parameter (e.g., "Monthly Bill", "Quarterly Bill")
    cost_euros: Decimal  # Extracted from invoice document
    iva_euros: Decimal  # Extracted from invoice document (VAT amount)
    deductible_percentage: float  # Provider-specific parameter (e.g., 0.0, 0.5, 1.0)
    file_name: str
    
    def __post_init__(self):
        """Validate the invoice metadata after initialization."""
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
    
    @property
    def total_euros(self) -> Decimal:
        """Calculate the total amount including VAT."""
        return self.cost_euros + self.iva_euros
    
    @property
    def deductible_amount(self) -> Decimal:
        """Calculate the deductible amount based on the percentage."""
        return self.total_euros * Decimal(str(self.deductible_percentage))
