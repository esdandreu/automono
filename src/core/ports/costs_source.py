"""
Costs source port interface.

Defines the contract for iterating over invoices from various providers.
"""

from typing import Iterator, Protocol, runtime_checkable

from ..domain.invoice import Invoice


@runtime_checkable
class CostsSource(Protocol):
    """Protocol interface for iterating over invoices from various providers."""
    
    def __iter__(self) -> Iterator[Invoice]:
        """
        Iterate over invoices from the provider in chronological order from newest to oldest.
        
        The iterator yields Invoice objects containing both metadata and file content.
        Each adapter implementation handles all the complex navigation, authentication, 
        and file retrieval internally.
        
        Yields:
            Invoice objects with complete metadata and file content
            
        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If there are network connectivity issues
            ProviderError: If the provider's system is unavailable
        """
        ...
