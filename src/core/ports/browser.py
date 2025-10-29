"""
Browser port interface.

Defines the contract for browser automation functionality in the application.
This allows for dependency injection and makes the browser system testable.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Protocol

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# Re-export commonly used selenium types for convenience
__all__ = ["Browser", "By", "WebElement"]


class Browser(Protocol):
    """Browser interface for dependency injection."""
    
    @abstractmethod
    def start(self) -> None:
        """Start the browser."""
        pass

    @property
    @abstractmethod
    def driver(self) -> webdriver.Chrome:
        """Get the browser driver."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the browser and clean up resources."""
        pass
    
    @abstractmethod
    def wait_for_element(self, by: By, value: str, timeout: int = 10) -> WebElement:
        """Wait for an element to be present and visible."""
        pass
    
    @abstractmethod
    def wait_for_clickable(self, by: By, value: str, timeout: int = 10) -> WebElement:
        """Wait for an element to be clickable."""
        pass
    
    @abstractmethod
    def wait_for_element_with_text(self, by: By, value: str, text: str, timeout: int = 10) -> WebElement:
        """Wait for an element to contain specific text."""
        pass
    
    @abstractmethod
    def get_download_dir(self) -> Path:
        """Get the download directory path."""
        pass
    
    @abstractmethod
    def __enter__(self):
        """Context manager entry."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
