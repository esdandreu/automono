"""
Invoice domain model.

Unified model containing metadata and artifact path for an invoice.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path


@dataclass
class Invoice:
    """Unified invoice model containing metadata and artifact path."""

    # Metadata fields
    invoice_date: datetime  # Extracted from invoice document
    concept: str  # Provider-specific parameter (e.g., "Luz Repsol")
    type: str  # Provider-specific parameter (e.g., "Suministros")
    cost_euros: Decimal  # Extracted from invoice document
    iva_euros: Decimal  # Extracted from invoice document (VAT amount)
    deductible_percentage: float  # Provider-specific parameter (e.g., 6.48%)

    # Artifact field
    path: Path

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

        # Validate artifact path
        self.path = Path(self.path)
        if not self.path.exists():
            raise ValueError(f"Artifact path {self.path} does not exist")
