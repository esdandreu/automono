"""
Application configuration settings.

Manages all configuration through environment variables with validation.
"""

from typing import Optional, Final

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Provider Credentials
    repsol_username: str = Field(..., env="REPSOL_USERNAME")
    repsol_password: str = Field(..., env="REPSOL_PASSWORD")
    digi_username: str = Field(..., env="DIGI_USERNAME")
    digi_password: str = Field(..., env="DIGI_PASSWORD")
    emivasa_username: str = Field(..., env="EMIVASA_USERNAME")
    emivasa_password: str = Field(..., env="EMIVASA_PASSWORD")
    
    # Google Services
    google_credentials_json: str = Field(..., env="GOOGLE_CREDENTIALS_JSON")
    google_sheets_id: str = Field(..., env="GOOGLE_SHEETS_ID")
    google_drive_folder_id: str = Field(..., env="GOOGLE_DRIVE_FOLDER_ID")
    
    # Microsoft Services
    microsoft_client_id: str = Field(..., env="MICROSOFT_CLIENT_ID")
    microsoft_client_secret: str = Field(..., env="MICROSOFT_CLIENT_SECRET")
    microsoft_tenant_id: str = Field(..., env="MICROSOFT_TENANT_ID")
    onedrive_folder_id: str = Field(..., env="ONEDRIVE_FOLDER_ID")
    
    # Application Settings
    headless_mode: bool = Field(True, env="HEADLESS_MODE")
    download_timeout: int = Field(300, env="DOWNLOAD_TIMEOUT")
    max_retries: int = Field(3, env="MAX_RETRIES")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Browser Settings
    browser_window_width: int = Field(1920, env="BROWSER_WINDOW_WIDTH")
    browser_window_height: int = Field(1080, env="BROWSER_WINDOW_HEIGHT")
    implicit_wait: int = Field(10, env="IMPLICIT_WAIT")
    page_load_timeout: int = Field(30, env="PAGE_LOAD_TIMEOUT")
    
    # Processing Settings
    max_invoices_per_run: int = Field(50, env="MAX_INVOICES_PER_RUN")
    invoice_lookback_days: int = Field(90, env="INVOICE_LOOKBACK_DAYS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings instance."""
    return settings
