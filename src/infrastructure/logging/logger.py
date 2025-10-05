"""
Structured logging configuration.

Provides consistent logging across the application with structured output.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from colorama import Fore, Style, init

from ..config.settings import get_settings

# Initialize colorama for colored output
init(autoreset=True)


def configure_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    
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
            structlog.processors.JSONRenderer() if settings.log_level == "DEBUG" else colorize_processor,
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
        level=getattr(logging, settings.log_level.upper()),
    )


def colorize_processor(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> str:
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


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
