"""
Simple print-based logger adapter implementation.

Implements the Logger port using simple print statements for lightweight logging.
"""

from typing import Any

from src.core.ports.logger import Logger

def message_with_kwargs(message: str, kwargs: Any) -> str:
    """Format a message with kwargs."""
    return f"{message} {kwargs}" if kwargs else message


class SimpleLogger(Logger):
    """Simple print-based logger implementation for testing and lightweight logging."""
    
    def __init__(self, name: str):
        """Initialize the simple logger with a name."""
        self.name = name
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        print(f"[DEBUG] {self.name}: {message_with_kwargs(message, kwargs)}")
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        print(f"[INFO] {self.name}: {message_with_kwargs(message, kwargs)}")
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        print(f"[WARNING] {self.name}: {message_with_kwargs(message, kwargs)}")
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        print(f"[ERROR] {self.name}: {message_with_kwargs(message, kwargs)}")
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message."""
        print(f"[CRITICAL] {self.name}: {message_with_kwargs(message, kwargs)}")
