"""
Archive result domain model.

Represents the result of archiving an invoice file to cloud storage.
"""

from dataclasses import dataclass
from typing import Optional, Final


@dataclass
class ArchiveResult:
    """Result of archiving an invoice file to cloud storage."""
    
    archive_id: str
    archive_type: str  # "google_drive", "onedrive"
    file_url: str
    success: bool
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate the archive result after initialization."""
        if not self.archive_id.strip():
            raise ValueError("Archive ID cannot be empty")
        
        if not self.archive_type.strip():
            raise ValueError("Archive type cannot be empty")
        
        if not self.file_url.strip():
            raise ValueError("File URL cannot be empty")
        
        if not self.success and not self.error_message:
            raise ValueError("Error message is required when success is False")
        
        if self.success and self.error_message:
            raise ValueError("Error message should not be set when success is True")
    
    @property
    def is_successful(self) -> bool:
        """Check if the archive operation was successful."""
        return self.success
    
    @property
    def is_failed(self) -> bool:
        """Check if the archive operation failed."""
        return not self.success
