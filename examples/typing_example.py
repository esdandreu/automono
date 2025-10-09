#!/usr/bin/env python3
"""
Example demonstrating the improved typing in the invoice automation system.

This example shows how the type annotations help with IDE support,
static analysis, and runtime type checking.
"""

from datetime import datetime
from decimal import Decimal
from typing import List

# Import our domain models with proper typing
from src.core.domain.invoice_metadata import InvoiceMetadata
from src.core.domain.registered_invoice import RegisteredInvoice, InvoiceStatus


def create_sample_invoice() -> InvoiceMetadata:
    """Create a sample invoice with proper typing."""
    return InvoiceMetadata(
        invoice_date=datetime(2024, 1, 15),
        concept="Electricity",
        type="Monthly Bill",
        cost_euros=Decimal("50.00"),
        iva_euros=Decimal("10.50"),
        deductible_percentage=1.0,
        file_name="repsol_202401_50.00.pdf"
    )


def create_sample_registered_invoice() -> RegisteredInvoice:
    """Create a sample registered invoice with proper typing."""
    return RegisteredInvoice(
        invoice_date=datetime(2024, 1, 15),
        concept="Electricity",
        type="Monthly Bill",
        cost_euros=Decimal("50.00"),
        iva_euros=Decimal("10.50"),
        deductible_percentage=1.0,
        file_hash="abc123def456",
        google_drive_id="drive_12345",
        onedrive_id="onedrive_67890",
        processed_date=datetime(2024, 1, 16),
        status="success"  # This is type-checked as InvoiceStatus
    )


def process_invoices(invoices: List[InvoiceMetadata]) -> List[RegisteredInvoice]:
    """Process a list of invoices with proper typing."""
    registered_invoices: List[RegisteredInvoice] = []
    
    for invoice in invoices:
        # Type-safe access to invoice properties
        total_amount = invoice.total_euros
        deductible_amount = invoice.deductible_amount
        
        # Create registered invoice with proper status typing
        status: InvoiceStatus = "success"  # Type-checked
        
        registered_invoice = RegisteredInvoice(
            invoice_date=invoice.invoice_date,
            concept=invoice.concept,
            type=invoice.type,
            cost_euros=invoice.cost_euros,
            iva_euros=invoice.iva_euros,
            deductible_percentage=invoice.deductible_percentage,
            file_hash="generated_hash",
            google_drive_id="drive_id",
            onedrive_id="onedrive_id",
            processed_date=datetime.now(),
            status=status
        )
        
        registered_invoices.append(registered_invoice)
    
    return registered_invoices


def demonstrate_type_safety():
    """Demonstrate type safety features."""
    print("🔍 Type Safety Demonstration")
    print("=" * 40)
    
    # Create sample data
    invoice = create_sample_invoice()
    registered_invoice = create_sample_registered_invoice()
    
    # Type-safe property access
    print(f"Invoice total: {invoice.total_euros}")
    print(f"Deductible amount: {invoice.deductible_amount}")
    print(f"Registered invoice status: {registered_invoice.status}")
    print(f"Is successful: {registered_invoice.is_successful}")
    
    # Type-safe list processing
    invoices = [invoice]
    processed = process_invoices(invoices)
    print(f"Processed {len(processed)} invoices")
    
    # Demonstrate type checking benefits
    print("\n✅ Type checking benefits:")
    print("- IDE autocomplete and error detection")
    print("- Static analysis with mypy")
    print("- Runtime type validation")
    print("- Better documentation and code clarity")


if __name__ == "__main__":
    demonstrate_type_safety()


