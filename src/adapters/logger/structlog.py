"""
Structlog logger adapter implementation.

Implements the Logger port using structlog for structured logging.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from colorama import Fore, Style, init

from src.core.ports.logger import Logger


class Structlog(Logger):
    """Structlog implementation of the Logger port."""
    
    _configured = False
    
    def __init__(self, name: str, log_level: str = "INFO"):
        """Initialize the structlog adapter with a logger name."""
        if not Structlog._configured:
            # Initialize colorama for colored output
            init(autoreset=True)
            self._configure_structlog(log_level)
            Structlog._configured = True
        
        self._logger = structlog.get_logger(name)
    
    def _configure_structlog(self, log_level: str) -> None:
        """Configure structlog for the application."""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if log_level == "DEBUG" else self._colorize_processor,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper()),
        )
    
    def _colorize_processor(self, logger: Any, method_name: str, event_dict: Dict[str, Any]) -> str:
        """Colorize log output for better readability."""
        level = event_dict.get("level", "").lower()
        
        if level == "error":
            color = Fore.RED
        elif level == "warning":
            color = Fore.YELLOW
        elif level == "info":
            color = Fore.GREEN
        elif level == "debug":
            color = Fore.CYAN
        else:
            color = Fore.WHITE
        
        # Format the log message
        timestamp = event_dict.get("timestamp", "")
        logger_name = event_dict.get("logger", "")
        message = event_dict.get("event", "")
        
        formatted_message = f"{color}{timestamp} [{level.upper()}] {logger_name}: {message}{Style.RESET_ALL}"
        
        # Add extra fields if present
        extra_fields = {k: v for k, v in event_dict.items() 
                       if k not in ["timestamp", "level", "logger", "event"]}
        
        if extra_fields:
            formatted_message += f" {extra_fields}"
        
        return formatted_message
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message."""
        self._logger.critical(message, **kwargs)