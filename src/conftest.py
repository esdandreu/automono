"""
Shared fixtures for the invoice automation tests.
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def artifacts_dir(project_root):
    """Return the test artifacts directory."""
    artifacts = project_root / "test-artifacts"
    artifacts.mkdir(exist_ok=True)
    return artifacts


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Include integration tests (test_integration*)"
    )


def pytest_configure(config):
    """Configure pytest based on command line arguments."""
    # Check if integration tests should be included
    include_integration = config.getoption("integration", default=False)
    
    if not include_integration:
        # Exclude integration tests by default
        existing_keyword = config.option.keyword or ""
        if existing_keyword:
            config.option.keyword = f"({existing_keyword}) and not integration"
        else:
            config.option.keyword = "not integration"