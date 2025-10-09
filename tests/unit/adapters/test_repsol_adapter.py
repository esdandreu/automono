"""
Unit tests for Repsol costs source adapter.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

from src.adapters.costs_sources.repsol.repsol_costs_source_adapter import RepsolCostsSourceAdapter
from src.core.domain.invoice_metadata import InvoiceMetadata


class TestRepsolCostsSourceAdapter:
    """Test cases for RepsolCostsSourceAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initialization."""
        selenium_service = Mock()
        adapter = RepsolCostsSourceAdapter("test_user", "test_pass", selenium_service)
        
        assert adapter.username == "test_user"
        assert adapter.password == "test_pass"
        assert adapter.selenium_service == selenium_service
        assert adapter.CONCEPT == "Electricity"
        assert adapter.TYPE == "Monthly Bill"
        assert adapter.DEDUCTIBLE_PERCENTAGE == 1.0
    
    def test_parse_date(self):
        """Test date parsing functionality."""
        selenium_service = Mock()
        adapter = RepsolCostsSourceAdapter("test_user", "test_pass", selenium_service)
        
        # Test DD/MM/YYYY format
        date = adapter._parse_date("15/01/2024")
        assert date == datetime(2024, 1, 15)
        
        # Test DD-MM-YYYY format
        date = adapter._parse_date("15-01-2024")
        assert date == datetime(2024, 1, 15)
        
        # Test YYYY/MM/DD format
        date = adapter._parse_date("2024/01/15")
        assert date == datetime(2024, 1, 15)
    
    def test_parse_amount(self):
        """Test amount parsing functionality."""
        selenium_service = Mock()
        adapter = RepsolCostsSourceAdapter("test_user", "test_pass", selenium_service)
        
        # Test with euro symbol
        amount = adapter._parse_amount("50,00 €")
        assert amount == Decimal("50.00")
        
        # Test with comma decimal separator
        amount = adapter._parse_amount("123,45")
        assert amount == Decimal("123.45")
        
        # Test with point decimal separator
        amount = adapter._parse_amount("123.45")
        assert amount == Decimal("123.45")
        
        # Test invalid amount
        amount = adapter._parse_amount("invalid")
        assert amount == Decimal("0.00")
    
    def test_invalid_date_parsing(self):
        """Test invalid date parsing raises error."""
        selenium_service = Mock()
        adapter = RepsolCostsSourceAdapter("test_user", "test_pass", selenium_service)
        
        with pytest.raises(ValueError, match="Could not parse date from"):
            adapter._parse_date("invalid date")
    
    def test_create_invoice_metadata(self):
        """Test creating invoice metadata with provider-specific values."""
        selenium_service = Mock()
        adapter = RepsolCostsSourceAdapter("test_user", "test_pass", selenium_service)
        
        # This would be called internally by the adapter
        metadata = InvoiceMetadata(
            invoice_date=datetime(2024, 1, 15),
            concept=adapter.CONCEPT,
            type=adapter.TYPE,
            cost_euros=Decimal("50.00"),
            iva_euros=Decimal("10.50"),
            deductible_percentage=adapter.DEDUCTIBLE_PERCENTAGE,
            file_name="repsol_202401_50.00.pdf"
        )
        
        assert metadata.concept == "Electricity"
        assert metadata.type == "Monthly Bill"
        assert metadata.deductible_percentage == 1.0
        assert metadata.deductible_amount == Decimal("60.50")  # 100% of total
