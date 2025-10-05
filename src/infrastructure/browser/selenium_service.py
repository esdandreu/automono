"""
Selenium browser automation service.

Provides a shared Selenium WebDriver service for web scraping operations.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from ..config.settings import get_settings
from ..logging.logger import get_logger

logger = get_logger(__name__)


class SeleniumService:
    """Selenium WebDriver service for browser automation."""
    
    def __init__(self):
        """Initialize the Selenium service."""
        self.settings = get_settings()
        self.driver: Optional[webdriver.Chrome] = None
        self.download_dir: Optional[Path] = None
    
    def start(self) -> webdriver.Chrome:
        """Start the Chrome WebDriver with configured options."""
        if self.driver is not None:
            logger.warning("WebDriver is already running")
            return self.driver
        
        # Create temporary download directory
        self.download_dir = Path(tempfile.mkdtemp())
        
        # Configure Chrome options
        chrome_options = ChromeOptions()
        
        if self.settings.headless_mode:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument(f"--window-size={self.settings.browser_window_width},{self.settings.browser_window_height}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Set download directory
        prefs = {
            "download.default_directory": str(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Initialize the driver
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Configure timeouts
        self.driver.implicitly_wait(self.settings.implicit_wait)
        self.driver.set_page_load_timeout(self.settings.page_load_timeout)
        
        logger.info("WebDriver started successfully", 
                   headless=self.settings.headless_mode,
                   download_dir=str(self.download_dir))
        
        return self.driver
    
    def stop(self) -> None:
        """Stop the WebDriver and cleanup resources."""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver stopped")
        
        # Cleanup download directory
        if self.download_dir and self.download_dir.exists():
            import shutil
            shutil.rmtree(self.download_dir, ignore_errors=True)
            self.download_dir = None
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> None:
        """Wait for an element to be present and visible."""
        timeout = timeout or self.settings.implicit_wait
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.presence_of_element_located((by, value)))
    
    def wait_for_clickable(self, by: By, value: str, timeout: Optional[int] = None) -> None:
        """Wait for an element to be clickable."""
        timeout = timeout or self.settings.implicit_wait
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.element_to_be_clickable((by, value)))
    
    def wait_for_download(self, filename: str, timeout: Optional[int] = None) -> Path:
        """Wait for a file to be downloaded."""
        timeout = timeout or self.settings.download_timeout
        wait = WebDriverWait(self.driver, timeout)
        
        def file_downloaded(driver):
            file_path = self.download_dir / filename
            return file_path.exists() and file_path.stat().st_size > 0
        
        wait.until(file_downloaded)
        return self.download_dir / filename
    
    def get_downloaded_file(self, filename: str) -> Optional[Path]:
        """Get a downloaded file if it exists."""
        if not self.download_dir:
            return None
        
        file_path = self.download_dir / filename
        if file_path.exists():
            return file_path
        
        return None
    
    def __enter__(self):
        """Context manager entry."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
