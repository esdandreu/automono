"""
Pytest configuration and shared fixtures for the invoice automation tests.
"""

import os
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def artifacts_dir(project_root):
    """Return the test artifacts directory."""
    artifacts = project_root / "tests" / "artifacts"
    artifacts.mkdir(exist_ok=True)
    return artifacts


@pytest.fixture(scope="session")
def test_credentials():
    """Return test credentials from environment variables."""
    return {
        "repsol_username": os.getenv("REPSOL_USERNAME"),
        "repsol_password": os.getenv("REPSOL_PASSWORD"),
        "digi_username": os.getenv("DIGI_USERNAME"),
        "digi_password": os.getenv("DIGI_PASSWORD"),
        "emivasa_username": os.getenv("EMIVASA_USERNAME"),
        "emivasa_password": os.getenv("EMIVASA_PASSWORD"),
    }


@pytest.fixture(scope="session")
def selenium_options():
    """Return Chrome options for headless testing."""
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    return options
