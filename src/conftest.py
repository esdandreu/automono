"""
Shared fixtures for the invoice automation tests.
"""

import pytest
import os
from pathlib import Path
from collections import namedtuple
from dotenv import load_dotenv
from src.adapters.browser.selenium import SeleniumBrowser
from src.adapters.config.environment_config import Env, get_env_str
from src.adapters.logger.simple import SimpleLogger
from scripts.encrypt_test_data import decrypt_file


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def load_env(project_root):
    """Load environment variables from .env file in project root."""
    load_dotenv(dotenv_path=project_root / ".env")


@pytest.fixture(scope="session")
def artifacts_dir(project_root):
    """Return the test artifacts directory."""
    artifacts = project_root / "test-artifacts"
    artifacts.mkdir(exist_ok=True)
    return artifacts


@pytest.fixture(scope="function")
def logger():
    """Create a logger instance for testing."""
    return SimpleLogger("test_integration")


@pytest.fixture(scope="function")
def config(request):
    """Create a configuration instance for testing."""
    TestConfig = namedtuple('TestConfig', [
        'repsol_username',
        'repsol_password',
        'headless_mode',
        'browser_window_width',
        'browser_window_height',
        'implicit_wait',
        'page_load_timeout'
    ])
    no_headless = request.config.getoption("--no-headless", default=False)
    return TestConfig(
        repsol_username=get_env_str(Env.REPSOL_USERNAME),
        repsol_password=get_env_str(Env.REPSOL_PASSWORD),
        headless_mode=not no_headless,
        browser_window_width=1920,
        browser_window_height=1080,
        implicit_wait=10,
        page_load_timeout=30
    )


@pytest.fixture(scope="function")
def browser(config, logger):
    """Create a browser instance for testing."""
    browser_instance = SeleniumBrowser(config, logger)
    yield browser_instance
    # Cleanup: ensure browser is stopped after test
    browser_instance.stop()


@pytest.fixture(scope="function")
def repsol_test_password(load_env):
    """Get the password for decrypting Repsol test data."""
    return os.getenv('REPSOL_PASSWORD')

@pytest.fixture(scope="function")
def decrypt_test_data(tmp_path):
    """Decrypt a file to a temporary file in pytest's temporary directory.
    
    Returns a function that decrypts a file and returns the path to the
    decrypted file. The decrypted file will be automatically cleaned up after
    the test executes.
    """
    def _decrypt(encrypted_file_path: Path, password: str) -> Path:
        """Decrypt a file to a temporary location.
        
        Args:
            encrypted_file_path: Path to the encrypted file
            password: Password for decryption
            
        Returns:
            Path to the decrypted temporary file
        """
        # Create a temporary file in pytest's tmp_path (automatically cleaned up)
        # Use the encrypted file's name with a prefix to avoid conflicts
        encrypted_path = Path(encrypted_file_path)
        temp_output = tmp_path / f"{encrypted_path.name}.decrypted"
        
        # Decrypt the file
        decrypt_file(encrypted_file_path, temp_output, password)
        
        return temp_output
    
    return _decrypt

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Include integration tests (test_integration*)"
    )
    parser.addoption(
        "--no-headless",
        action="store_true",
        default=False,
        help="Run browser tests in non-headless mode (rendering visible)"
    )


def pytest_configure(config):
    """Configure pytest based on command line arguments."""
    # Check if integration tests should be included
    include_integration = config.getoption("--integration", default=False)
    
    if not include_integration:
        # Exclude integration tests by default
        existing_keyword = config.option.keyword or ""
        if existing_keyword:
            config.option.keyword = f"({existing_keyword}) and not integration"
        else:
            config.option.keyword = "not integration"