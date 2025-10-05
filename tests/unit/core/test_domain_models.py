"""
Unit tests for domain models.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.core.domain.invoice_metadata import InvoiceMetadata
from src.core.domain.invoice_file import InvoiceFile
from src.core.domain.archive_result import ArchiveResult
from src.core.domain.registered_invoice import RegisteredInvoice


class TestInvoiceMetadata:
    """Test cases for InvoiceMetadata."""
    
    def test_valid_invoice_metadata(self):
        """Test creating valid invoice metadata."""
        metadata = InvoiceMetadata(
            invoice_date=datetime(2024, 1, 15),
            concept="Electricity",
            type="Monthly Bill",
            cost_euros=Decimal("50.00"),
            iva_euros=Decimal("10.50"),
            deductible_percentage=1.0,
            file_name="invoice_2024_01.pdf"
        )
        
        assert metadata.invoice_date == datetime(2024, 1, 15)
        assert metadata.concept == "Electricity"
        assert metadata.type == "Monthly Bill"
        assert metadata.cost_euros == Decimal("50.00")
        assert metadata.iva_euros == Decimal("10.50")
        assert metadata.deductible_percentage == 1.0
        assert metadata.file_name == "invoice_2024_01.pdf"
    
    def test_total_euros_calculation(self):
        """Test total euros calculation."""
        metadata = InvoiceMetadata(
            invoice_date=datetime(2024, 1, 15),
            concept="Electricity",
            type="Monthly Bill",
            cost_euros=Decimal("50.00"),
            iva_euros=Decimal("10.50"),
            deductible_percentage=1.0,
            file_name="invoice_2024_01.pdf"
        )
        
        assert metadata.total_euros == Decimal("60.50")
    
    def test_deductible_amount_calculation(self):
        """Test deductible amount calculation."""
        metadata = InvoiceMetadata(
            invoice_date=datetime(2024, 1, 15),
            concept="Electricity",
            type="Monthly Bill",
            cost_euros=Decimal("50.00"),
            iva_euros=Decimal("10.50"),
            deductible_percentage=0.5,
            file_name="invoice_2024_01.pdf"
        )
        
        assert metadata.deductible_amount == Decimal("30.25")
    
    def test_invalid_deductible_percentage(self):
        """Test validation of deductible percentage."""
        with pytest.raises(ValueError, match="Deductible percentage must be between 0.0 and 1.0"):
            InvoiceMetadata(
                invoice_date=datetime(2024, 1, 15),
                concept="Electricity",
                type="Monthly Bill",
                cost_euros=Decimal("50.00"),
                iva_euros=Decimal("10.50"),
                deductible_percentage=1.5,
                file_name="invoice_2024_01.pdf"
            )
    
    def test_negative_cost_amount(self):
        """Test validation of negative cost amount."""
        with pytest.raises(ValueError, match="Cost amount cannot be negative"):
            InvoiceMetadata(
                invoice_date=datetime(2024, 1, 15),
                concept="Electricity",
                type="Monthly Bill",
                cost_euros=Decimal("-50.00"),
                iva_euros=Decimal("10.50"),
                deductible_percentage=1.0,
                file_name="invoice_2024_01.pdf"
            )


class TestInvoiceFile:
    """Test cases for InvoiceFile."""
    
    def test_valid_invoice_file(self):
        """Test creating valid invoice file."""
        content = b"PDF content here"
        file = InvoiceFile.from_content(content, "test.pdf")
        
        assert file.content == content
        assert file.file_name == "test.pdf"
        assert file.content_type == "application/pdf"
        assert file.size == len(content)
        assert file.hash_md5 == "d41d8cd98f00b204e9800998ecf8427e"  # MD5 of empty string
        assert file.hash_sha256 == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # SHA256 of empty string
    
    def test_empty_content_validation(self):
        """Test validation of empty content."""
        with pytest.raises(ValueError, match="File content cannot be empty"):
            InvoiceFile(
                content=b"",
                file_name="test.pdf",
                content_type="application/pdf",
                size=0,
                hash_md5="d41d8cd98f00b204e9800998ecf8427e",
                hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            )


class TestArchiveResult:
    """Test cases for ArchiveResult."""
    
    def test_successful_archive_result(self):
        """Test creating successful archive result."""
        result = ArchiveResult(
            archive_id="12345",
            archive_type="google_drive",
            file_url="https://drive.google.com/file/12345",
            success=True
        )
        
        assert result.archive_id == "12345"
        assert result.archive_type == "google_drive"
        assert result.file_url == "https://drive.google.com/file/12345"
        assert result.success is True
        assert result.error_message is None
        assert result.is_successful is True
        assert result.is_failed is False
    
    def test_failed_archive_result(self):
        """Test creating failed archive result."""
        result = ArchiveResult(
            archive_id="12345",
            archive_type="google_drive",
            file_url="",
            success=False,
            error_message="Upload failed"
        )
        
        assert result.success is False
        assert result.error_message == "Upload failed"
        assert result.is_successful is False
        assert result.is_failed is True
    
    def test_failed_result_without_error_message(self):
        """Test validation of failed result without error message."""
        with pytest.raises(ValueError, match="Error message is required when success is False"):
            ArchiveResult(
                archive_id="12345",
                archive_type="google_drive",
                file_url="",
                success=False
            )


class TestRegisteredInvoice:
    """Test cases for RegisteredInvoice."""
    
    def test_valid_registered_invoice(self):
        """Test creating valid registered invoice."""
        invoice = RegisteredInvoice(
            invoice_date=datetime(2024, 1, 15),
            concept="Electricity",
            type="Monthly Bill",
            cost_euros=Decimal("50.00"),
            iva_euros=Decimal("10.50"),
            deductible_percentage=1.0,
            file_hash="abc123",
            google_drive_id="drive123",
            onedrive_id="onedrive123",
            processed_date=datetime(2024, 1, 16),
            status="success"
        )
        
        assert invoice.invoice_date == datetime(2024, 1, 15)
        assert invoice.concept == "Electricity"
        assert invoice.cost_euros == Decimal("50.00")
        assert invoice.iva_euros == Decimal("10.50")
        assert invoice.deductible_percentage == 1.0
        assert invoice.file_hash == "abc123"
        assert invoice.google_drive_id == "drive123"
        assert invoice.onedrive_id == "onedrive123"
        assert invoice.status == "success"
        assert invoice.is_successful is True
        assert invoice.has_google_drive_id is True
        assert invoice.has_onedrive_id is True
    
    def test_invalid_status(self):
        """Test validation of invalid status."""
        with pytest.raises(ValueError, match="Status must be 'success', 'failed', or 'skipped'"):
            RegisteredInvoice(
                invoice_date=datetime(2024, 1, 15),
                concept="Electricity",
                type="Monthly Bill",
                cost_euros=Decimal("50.00"),
                iva_euros=Decimal("10.50"),
                deductible_percentage=1.0,
                file_hash="abc123",
                google_drive_id="drive123",
                onedrive_id="onedrive123",
                processed_date=datetime(2024, 1, 16),
                status="invalid"
            )
