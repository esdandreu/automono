"""
Registered invoice domain model.

Represents an invoice that has been processed and registered in the system.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class RegisteredInvoice:
    """Represents an invoice that has been processed and registered."""
    
    invoice_date: datetime
    concept: str
    type: str
    cost_euros: Decimal
    iva_euros: Decimal
    deductible_percentage: float
    file_hash: str
    google_drive_id: Optional[str]
    onedrive_id: Optional[str]
    processed_date: datetime
    status: str  # "success", "failed", "skipped"
    
    def __post_init__(self):
        """Validate the registered invoice after initialization."""
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
        
        if not self.file_hash.strip():
            raise ValueError("File hash cannot be empty")
        
        if self.status not in ["success", "failed", "skipped"]:
            raise ValueError("Status must be 'success', 'failed', or 'skipped'")
    
    @property
    def total_euros(self) -> Decimal:
        """Calculate the total amount including VAT."""
        return self.cost_euros + self.iva_euros
    
    @property
    def deductible_amount(self) -> Decimal:
        """Calculate the deductible amount based on the percentage."""
        return self.total_euros * Decimal(str(self.deductible_percentage))
    
    @property
    def is_successful(self) -> bool:
        """Check if the invoice was processed successfully."""
        return self.status == "success"
    
    @property
    def has_google_drive_id(self) -> bool:
        """Check if the invoice has a Google Drive ID."""
        return self.google_drive_id is not None and self.google_drive_id.strip() != ""
    
    @property
    def has_onedrive_id(self) -> bool:
        """Check if the invoice has a OneDrive ID."""
        return self.onedrive_id is not None and self.onedrive_id.strip() != ""
