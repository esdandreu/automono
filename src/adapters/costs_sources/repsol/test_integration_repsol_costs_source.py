import pytest
from src.adapters.costs_sources.repsol.repsol_costs_source import RepsolCostsSource


@pytest.mark.integration
def test_repsol_costs_source(config, browser, logger, artifacts_dir):
    """Test the Repsol costs source integration."""
    source = RepsolCostsSource(
        config, browser, logger, str(artifacts_dir)
    )
    invoice_count = 0
    for invoice in source:
        print("Invoice:", invoice)
        invoice_count += 1
        if invoice_count >= 3:  # Process first 3 invoices
            break
    print("test_repsol_costs_source finished")
