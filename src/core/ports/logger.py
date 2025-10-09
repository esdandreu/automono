"""
Logger port interface.

Defines the contract for logging functionality in the application.
This allows for dependency injection and makes the logging system testable.
"""

from abc import ABC, abstractmethod
from typing import Any


class Logger(ABC):
    """Abstract logger interface for dependency injection."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message."""
        pass
