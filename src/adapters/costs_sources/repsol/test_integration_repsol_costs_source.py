import pytest
from src.adapters.costs_sources.repsol.repsol_costs_source import RepsolCostsSource


@pytest.mark.integration
def test_repsol_costs_source(config, browser, logger):
    """Test the Repsol costs source integration."""
    source = RepsolCostsSource(
        config, browser, logger,
    )
    for invoice in source:
        print("Invoice:", invoice)
        break
    print("test_repsol_costs_source finished")
