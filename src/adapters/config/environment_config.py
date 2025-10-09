"""
Environment-based configuration adapter.

Implements the Config port using environment variables.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Final

from src.core.ports.config import Config


class Env(str, Enum):
    """Environment variable names as string enum."""
    
    # Provider Credentials
    REPSOL_USERNAME = "REPSOL_USERNAME"
    REPSOL_PASSWORD = "REPSOL_PASSWORD"
    DIGI_USERNAME = "DIGI_USERNAME"
    DIGI_PASSWORD = "DIGI_PASSWORD"
    EMIVASA_USERNAME = "EMIVASA_USERNAME"
    EMIVASA_PASSWORD = "EMIVASA_PASSWORD"
    
    # Google Services
    GOOGLE_CREDENTIALS_JSON = "GOOGLE_CREDENTIALS_JSON"
    GOOGLE_SHEETS_ID = "GOOGLE_SHEETS_ID"
    GOOGLE_DRIVE_FOLDER_ID = "GOOGLE_DRIVE_FOLDER_ID"
    
    # Microsoft Services
    MICROSOFT_CLIENT_ID = "MICROSOFT_CLIENT_ID"
    MICROSOFT_CLIENT_SECRET = "MICROSOFT_CLIENT_SECRET"
    MICROSOFT_TENANT_ID = "MICROSOFT_TENANT_ID"
    ONEDRIVE_FOLDER_ID = "ONEDRIVE_FOLDER_ID"
    
    # Application Settings
    HEADLESS_MODE = "HEADLESS_MODE"
    DOWNLOAD_TIMEOUT = "DOWNLOAD_TIMEOUT"
    MAX_RETRIES = "MAX_RETRIES"
    LOG_LEVEL = "LOG_LEVEL"
    
    # Browser Settings
    BROWSER_WINDOW_WIDTH = "BROWSER_WINDOW_WIDTH"
    BROWSER_WINDOW_HEIGHT = "BROWSER_WINDOW_HEIGHT"
    IMPLICIT_WAIT = "IMPLICIT_WAIT"
    PAGE_LOAD_TIMEOUT = "PAGE_LOAD_TIMEOUT"
    
    # Processing Settings
    MAX_INVOICES_PER_RUN = "MAX_INVOICES_PER_RUN"
    INVOICE_LOOKBACK_DAYS = "INVOICE_LOOKBACK_DAYS"


@dataclass
class EnvironmentConfig(Config):
    """Environment-based configuration adapter."""
    
    # Provider Credentials
    repsol_username: str
    repsol_password: str
    digi_username: str
    digi_password: str
    emivasa_username: str
    emivasa_password: str
    
    # Google Services
    google_credentials_json: str
    google_sheets_id: str
    google_drive_folder_id: str
    
    # Microsoft Services
    microsoft_client_id: str
    microsoft_client_secret: str
    microsoft_tenant_id: str
    onedrive_folder_id: str
    
    # Application Settings
    headless_mode: bool = True
    download_timeout: int = 300
    max_retries: int = 3
    log_level: str = "INFO"
    
    # Browser Settings
    browser_window_width: int = 1920
    browser_window_height: int = 1080
    implicit_wait: int = 10
    page_load_timeout: int = 30
    
    # Processing Settings
    max_invoices_per_run: int = 50
    invoice_lookback_days: int = 90
    
    def __post_init__(self):
        """Validate settings after initialization."""
        # Validate numeric fields
        if self.download_timeout <= 0:
            raise ValueError("download_timeout must be positive")
        
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        
        if self.browser_window_width <= 0 or self.browser_window_height <= 0:
            raise ValueError("browser window dimensions must be positive")
        
        if self.implicit_wait <= 0 or self.page_load_timeout <= 0:
            raise ValueError("timeout values must be positive")
        
        if self.max_invoices_per_run <= 0:
            raise ValueError("max_invoices_per_run must be positive")
        
        if self.invoice_lookback_days <= 0:
            raise ValueError("invoice_lookback_days must be positive")
        
        # Validate log level
        valid_log_levels: Final[tuple[str, ...]] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"log_level must be one of {valid_log_levels}")


def get_env_str(key: str, default: str = "") -> str:
    """Get environment variable as string."""
    return os.getenv(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int) -> int:
    """Get integer environment variable."""
    value = os.getenv(key, str(default))
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be an integer, got: {value}")


def create_environment_config() -> EnvironmentConfig:
    """Create environment configuration instance from environment variables."""
    return EnvironmentConfig(
        # Provider Credentials
        repsol_username=get_env_str(Env.REPSOL_USERNAME),
        repsol_password=get_env_str(Env.REPSOL_PASSWORD),
        digi_username=get_env_str(Env.DIGI_USERNAME),
        digi_password=get_env_str(Env.DIGI_PASSWORD),
        emivasa_username=get_env_str(Env.EMIVASA_USERNAME),
        emivasa_password=get_env_str(Env.EMIVASA_PASSWORD),
        
        # Google Services
        google_credentials_json=get_env_str(Env.GOOGLE_CREDENTIALS_JSON),
        google_sheets_id=get_env_str(Env.GOOGLE_SHEETS_ID),
        google_drive_folder_id=get_env_str(Env.GOOGLE_DRIVE_FOLDER_ID),
        
        # Microsoft Services
        microsoft_client_id=get_env_str(Env.MICROSOFT_CLIENT_ID),
        microsoft_client_secret=get_env_str(Env.MICROSOFT_CLIENT_SECRET),
        microsoft_tenant_id=get_env_str(Env.MICROSOFT_TENANT_ID),
        onedrive_folder_id=get_env_str(Env.ONEDRIVE_FOLDER_ID),
        
        # Application Settings
        headless_mode=get_env_bool(Env.HEADLESS_MODE, True),
        download_timeout=get_env_int(Env.DOWNLOAD_TIMEOUT, 300),
        max_retries=get_env_int(Env.MAX_RETRIES, 3),
        log_level=get_env_str(Env.LOG_LEVEL, "INFO"),
        
        # Browser Settings
        browser_window_width=get_env_int(Env.BROWSER_WINDOW_WIDTH, 1920),
        browser_window_height=get_env_int(Env.BROWSER_WINDOW_HEIGHT, 1080),
        implicit_wait=get_env_int(Env.IMPLICIT_WAIT, 10),
        page_load_timeout=get_env_int(Env.PAGE_LOAD_TIMEOUT, 30),
        
        # Processing Settings
        max_invoices_per_run=get_env_int(Env.MAX_INVOICES_PER_RUN, 50),
        invoice_lookback_days=get_env_int(Env.INVOICE_LOOKBACK_DAYS, 90),
    )
