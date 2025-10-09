"""
Invoice archive port interface.

Defines the contract for storing invoice files in cloud storage.
"""

from typing import Protocol, runtime_checkable

from ..domain.archive_result import ArchiveResult
from ..domain.invoice_file import InvoiceFile
from ..domain.invoice_metadata import InvoiceMetadata


@runtime_checkable
class InvoiceArchive(Protocol):
    """Protocol interface for storing invoice files in cloud storage."""
    
    def archive_invoice(self, invoice_file: InvoiceFile, metadata: InvoiceMetadata) -> ArchiveResult:
        """
        Store an invoice file in the cloud storage.
        
        Args:
            invoice_file: The invoice file to store
            metadata: The invoice metadata
            
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
