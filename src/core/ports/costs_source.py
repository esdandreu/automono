"""
Costs source port interface.

Defines the contract for fetching invoices from various providers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from ..domain.invoice_file import InvoiceFile
from ..domain.invoice_metadata import InvoiceMetadata


class CostsSource(ABC):
    """Abstract interface for fetching invoices from various providers."""
    
    @abstractmethod
    def get_available_invoices(self, since_date: datetime) -> List[InvoiceMetadata]:
        """
        Get a list of available invoices since the specified date.
        
        Args:
            since_date: Only return invoices from this date onwards
            
        Returns:
            List of invoice metadata objects
            
        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If there are network connectivity issues
            ProviderError: If the provider's system is unavailable
        """
        pass
    
    @abstractmethod
    def download_invoice(self, invoice_metadata: InvoiceMetadata) -> InvoiceFile:
        """
        Download the actual invoice file for the given metadata.
        
        This method handles all the complex navigation, authentication, 
        and file retrieval internally. Each adapter implementation manages 
        its own provider-specific download process.
        
        Args:
            invoice_metadata: The metadata for the invoice to download
            
        Returns:
            The downloaded invoice file
            
        Raises:
            AuthenticationError: If authentication fails during download
            NetworkError: If there are network connectivity issues
            ProviderError: If the provider's system is unavailable
            FileNotFoundError: If the invoice file cannot be found
        """
        pass
