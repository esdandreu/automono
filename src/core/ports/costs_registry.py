"""
Costs registry port interface.

Defines the contract for managing invoice records and tracking.
"""

from datetime import datetime
from typing import List, Protocol, runtime_checkable

from ..domain.archive_result import ArchiveResult
from ..domain.invoice import Invoice
from ..domain.registered_invoice import RegisteredInvoice


@runtime_checkable
class CostsRegistry(Protocol):
    """Protocol interface for managing invoice records and tracking."""
    
    def get_registered_invoices(self, since_date: datetime) -> List[RegisteredInvoice]:
        """
        Get a list of registered invoices since the specified date.
        
        Args:
            since_date: Only return invoices from this date onwards
            
        Returns:
            List of registered invoice objects
            
        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If there are network connectivity issues
            RegistryError: If the registry service is unavailable
        """
        ...
    
    def register_invoice(self, invoice: Invoice, archive_results: List[ArchiveResult]) -> bool:
        """
        Register a new invoice with its archive results.
        
        Args:
            invoice: The invoice to register (containing both metadata and file content)
            archive_results: List of archive results from storage services
            
        Returns:
            True if registration was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If there are network connectivity issues
            RegistryError: If the registry service is unavailable
            DuplicateError: If the invoice is already registered
        """
        ...
