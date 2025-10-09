"""
Invoice archive port interface.

Defines the contract for storing invoice files in cloud storage.
"""

from typing import Protocol, runtime_checkable

from ..domain.archive_result import ArchiveResult
from ..domain.invoice import Invoice


@runtime_checkable
class InvoiceArchive(Protocol):
    """Protocol interface for storing invoice files in cloud storage."""
    
    def archive_invoice(self, invoice: Invoice) -> ArchiveResult:
        """
        Store an invoice in the cloud storage.
        
        Args:
            invoice: The invoice to store (containing both metadata and file content)
            
        Returns:
            Archive result containing the archive ID and file URL
            
        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If there are network connectivity issues
            StorageError: If the storage service is unavailable
            QuotaExceededError: If storage quota is exceeded
        """
        ...
    
    def get_invoice_url(self, archive_id: str) -> str:
        """
        Get the URL for an archived invoice.
        
        Args:
            archive_id: The archive ID of the stored invoice
            
        Returns:
            The URL to access the archived invoice
            
        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If the archive ID is not found
            NetworkError: If there are network connectivity issues
        """
        ...
