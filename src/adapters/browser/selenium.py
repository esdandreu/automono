"""
Selenium browser automation adapter.

Provides a shared Selenium WebDriver service for web scraping operations.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Final

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from src.core.ports.config import Config
from src.core.ports.logger import Logger
from src.core.ports.browser import Browser, By


class SeleniumAdapter:
    """Selenium WebDriver adapter for browser automation."""
    
    def __init__(self, config: Config, logger: Logger):
        """Initialize the Selenium adapter."""
        self.config = config
        self.logger = logger
        self.driver: Optional[webdriver.Chrome] = None
        self.download_dir: Optional[Path] = None
    
    def start(self) -> webdriver.Chrome:
        """Start the Chrome WebDriver with configured options."""
        if self.driver is not None:
            self.logger.warning("WebDriver is already running")
            return self.driver
        
        self.logger.info("Starting Chrome WebDriver")
        
        # Create download directory
        self.download_dir = Path(tempfile.mkdtemp())
        self.logger.debug("Created download directory", download_dir=str(self.download_dir))
        
        # Configure Chrome options
        chrome_options = ChromeOptions()
        
        if self.config.headless_mode:
            chrome_options.add_argument("--headless")
            self.logger.debug("Running in headless mode")
        
        # Set window size
        chrome_options.add_argument(f"--window-size={self.config.browser_window_width},{self.config.browser_window_height}")
        
        # Set download directory
        prefs = {
            "download.default_directory": str(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Additional options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        
        # Initialize the driver
        try:
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.implicitly_wait(self.config.implicit_wait)
            self.driver.set_page_load_timeout(self.config.page_load_timeout)
            
            self.logger.info("Chrome WebDriver started successfully")
            return self.driver
            
        except Exception as e:
            self.logger.error("Failed to start Chrome WebDriver", error=str(e))
            raise
    
    def stop(self) -> None:
        """Stop the WebDriver and clean up resources."""
        if self.driver is not None:
            self.logger.info("Stopping Chrome WebDriver")
            self.driver.quit()
            self.driver = None
        
        # Clean up download directory
        if self.download_dir and self.download_dir.exists():
            import shutil
            shutil.rmtree(self.download_dir)
            self.logger.debug("Cleaned up download directory")
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10) -> None:
        """Wait for an element to be present and visible."""
        if self.driver is None:
            raise RuntimeError("WebDriver is not started")
        
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.presence_of_element_located((by, value)))
    
    def wait_for_clickable(self, by: By, value: str, timeout: int = 10) -> None:
        """Wait for an element to be clickable."""
        if self.driver is None:
            raise RuntimeError("WebDriver is not started")
        
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.element_to_be_clickable((by, value)))
    
    def get_download_dir(self) -> Path:
        """Get the download directory path."""
        if self.download_dir is None:
            raise RuntimeError("WebDriver is not started")
        return self.download_dir
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
