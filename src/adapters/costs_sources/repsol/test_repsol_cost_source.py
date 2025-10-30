"""
Unit tests for Repsol costs source.

These tests use encrypted test data to avoid exposing real invoice information.
"""

from decimal import Decimal
from pathlib import Path
import datetime
from unittest.mock import Mock

from src.adapters.costs_sources.repsol.repsol_costs_source import RepsolCostsSource
from src.core.domain.invoice import Invoice


def test_extract_metadata_from_pdf_file(
    logger, decrypt_test_data, repsol_test_password
):
    """Test metadata extraction using real encrypted test PDFs."""
    test_data = Path(__file__).parent / "test_data" / "repsol_invoice.encrypted"

    # Create RepsolCostsSource instance
    repsol_source = RepsolCostsSource(
        config=Mock(),
        browser=Mock(),
        logger=logger,
        artifacts_dir="/tmp/test_artifacts",
    )

    # Test with the repsol invoice
    temp_pdf_path = decrypt_test_data(test_data, repsol_test_password)

    # Extract metadata
    invoice = repsol_source._extract_metadata_from_pdf_file(str(temp_pdf_path))

    # Verify basic structure
    assert isinstance(invoice, Invoice)
    assert invoice.invoice_date == datetime.datetime(2025, 10, 28)
    assert invoice.concept == "Luz Repsol"
    assert invoice.type == "Suministros"
    assert invoice.cost_euros == Decimal("60.52")
    assert invoice.iva_euros == Decimal("10.50")
    assert invoice.path == temp_pdf_path
