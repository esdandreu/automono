"""
Configuration port interface.

Defines the contract for configuration functionality in the application.
This allows for dependency injection and makes the configuration system testable.
"""

from abc import abstractmethod
from typing import Protocol


class Config(Protocol):
    """Configuration interface for dependency injection."""
    
    # Provider Credentials
    @property
    @abstractmethod
    def repsol_username(self) -> str:
        """Repsol username."""
        pass
    
    @property
    @abstractmethod
    def repsol_password(self) -> str:
        """Repsol password."""
        pass
    
    @property
    @abstractmethod
    def digi_username(self) -> str:
        """Digi username."""
        pass
    
    @property
    @abstractmethod
    def digi_password(self) -> str:
        """Digi password."""
        pass
    
    @property
    @abstractmethod
    def emivasa_username(self) -> str:
        """Emivasa username."""
        pass
    
    @property
    @abstractmethod
    def emivasa_password(self) -> str:
        """Emivasa password."""
        pass
    
    # Google Services
    @property
    @abstractmethod
    def google_credentials_json(self) -> str:
        """Google credentials JSON."""
        pass
    
    @property
    @abstractmethod
    def google_sheets_id(self) -> str:
        """Google Sheets ID."""
        pass
    
    @property
    @abstractmethod
    def google_drive_folder_id(self) -> str:
        """Google Drive folder ID."""
        pass
    
    # Microsoft Services
    @property
    @abstractmethod
    def microsoft_client_id(self) -> str:
        """Microsoft client ID."""
        pass
    
    @property
    @abstractmethod
    def microsoft_client_secret(self) -> str:
        """Microsoft client secret."""
        pass
    
    @property
    @abstractmethod
    def microsoft_tenant_id(self) -> str:
        """Microsoft tenant ID."""
        pass
    
    @property
    @abstractmethod
    def onedrive_folder_id(self) -> str:
        """OneDrive folder ID."""
        pass
    
    # Application Settings
    @property
    @abstractmethod
    def headless_mode(self) -> bool:
        """Headless mode setting."""
        pass
    
    @property
    @abstractmethod
    def download_timeout(self) -> int:
        """Download timeout in seconds."""
        pass
    
    @property
    @abstractmethod
    def max_retries(self) -> int:
        """Maximum retry attempts."""
        pass
    
    @property
    @abstractmethod
    def log_level(self) -> str:
        """Log level."""
        pass
    
    # Browser Settings
    @property
    @abstractmethod
    def browser_window_width(self) -> int:
        """Browser window width."""
        pass
    
    @property
    @abstractmethod
    def browser_window_height(self) -> int:
        """Browser window height."""
        pass
    
    @property
    @abstractmethod
    def implicit_wait(self) -> int:
        """Implicit wait timeout."""
        pass
    
    @property
    @abstractmethod
    def page_load_timeout(self) -> int:
        """Page load timeout."""
        pass
    
    # Processing Settings
    @property
    @abstractmethod
    def max_invoices_per_run(self) -> int:
        """Maximum invoices per run."""
        pass
    
    @property
    @abstractmethod
    def invoice_lookback_days(self) -> int:
        """Invoice lookback days."""
        pass
