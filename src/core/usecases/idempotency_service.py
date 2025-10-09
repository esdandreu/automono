"""
Idempotency service use case.

Ensures no duplicate processing and provides idempotent operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Final

from ..domain.invoice_metadata import InvoiceMetadata
from ..domain.registered_invoice import RegisteredInvoice
from ..ports.costs_registry import CostsRegistry
from ...infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class IdempotencyService:
    """Service for ensuring idempotent invoice processing."""
    
    def __init__(self, costs_registry: CostsRegistry):
        """Initialize the idempotency service."""
        self.costs_registry = costs_registry
        self.logger = logger
    
    def filter_new_invoices(self, invoices: List[InvoiceMetadata], since_date: Optional[datetime] = None) -> List[InvoiceMetadata]:
        """
        Filter out invoices that have already been processed.
        
        Args:
            invoices: List of invoices to check
            since_date: Only check invoices from this date onwards
            
        Returns:
            List of invoices that haven't been processed yet
        """
        if not invoices:
            return []
        
        # Get registered invoices from the registry
        lookback_date = since_date or (datetime.now() - timedelta(days=90))
        registered_invoices = self.costs_registry.get_registered_invoices(lookback_date)
        
        # Create a set of registered invoice keys for fast lookup
        registered_keys = {
            self._create_invoice_key(reg_invoice) 
            for reg_invoice in registered_invoices
        }
        
        # Filter out already processed invoices
        new_invoices = []
        for invoice in invoices:
            invoice_key = self._create_invoice_key_from_metadata(invoice)
            
            if invoice_key not in registered_keys:
                new_invoices.append(invoice)
                self.logger.debug("Invoice is new", 
                                invoice_key=invoice_key,
                                invoice_date=invoice.invoice_date.isoformat())
            else:
                self.logger.debug("Invoice already processed, skipping",
                                invoice_key=invoice_key,
                                invoice_date=invoice.invoice_date.isoformat())
        
        self.logger.info("Filtered invoices for processing",
                        total_invoices=len(invoices),
                        new_invoices=len(new_invoices),
                        already_processed=len(invoices) - len(new_invoices))
        
        return new_invoices
    
    def is_invoice_processed(self, invoice: InvoiceMetadata) -> bool:
        """
        Check if a specific invoice has already been processed.
        
        Args:
            invoice: The invoice to check
            
        Returns:
            True if the invoice has been processed, False otherwise
        """
        lookback_date = datetime.now() - timedelta(days=90)
        registered_invoices = self.costs_registry.get_registered_invoices(lookback_date)
        
        invoice_key = self._create_invoice_key_from_metadata(invoice)
        
        for reg_invoice in registered_invoices:
            if self._create_invoice_key(reg_invoice) == invoice_key:
                return True
        
        return False
    
    def _create_invoice_key(self, registered_invoice: RegisteredInvoice) -> str:
        """Create a unique key for a registered invoice."""
        return f"{registered_invoice.invoice_date.date()}_{registered_invoice.concept}_{registered_invoice.type}_{registered_invoice.cost_euros}"
    
    def _create_invoice_key_from_metadata(self, invoice: InvoiceMetadata) -> str:
        """Create a unique key for an invoice metadata."""
        return f"{invoice.invoice_date.date()}_{invoice.concept}_{invoice.type}_{invoice.cost_euros}"
    
    def get_processing_statistics(self, since_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get statistics about invoice processing.
        
        Args:
            since_date: Only include invoices from this date onwards
            
        Returns:
            Dictionary with processing statistics
        """
        lookback_date = since_date or (datetime.now() - timedelta(days=90))
        registered_invoices = self.costs_registry.get_registered_invoices(lookback_date)
        
        total_invoices = len(registered_invoices)
        successful_invoices = len([inv for inv in registered_invoices if inv.status == "success"])
        failed_invoices = len([inv for inv in registered_invoices if inv.status == "failed"])
        skipped_invoices = len([inv for inv in registered_invoices if inv.status == "skipped"])
        
        # Group by concept
        concept_stats = {}
        for invoice in registered_invoices:
            concept = invoice.concept
            if concept not in concept_stats:
                concept_stats[concept] = {"total": 0, "successful": 0, "failed": 0, "skipped": 0}
            
            concept_stats[concept]["total"] += 1
            concept_stats[concept][invoice.status] += 1
        
        # Calculate total amounts
        total_cost = sum(inv.cost_euros for inv in registered_invoices if inv.status == "success")
        total_iva = sum(inv.iva_euros for inv in registered_invoices if inv.status == "success")
        total_deductible = sum(inv.deductible_amount for inv in registered_invoices if inv.status == "success")
        
        statistics = {
            "total_invoices": total_invoices,
            "successful_invoices": successful_invoices,
            "failed_invoices": failed_invoices,
            "skipped_invoices": skipped_invoices,
            "success_rate": (successful_invoices / total_invoices * 100) if total_invoices > 0 else 0,
            "concept_breakdown": concept_stats,
            "total_cost_euros": float(total_cost),
            "total_iva_euros": float(total_iva),
            "total_deductible_euros": float(total_deductible),
            "period_start": lookback_date.isoformat(),
            "period_end": datetime.now().isoformat()
        }
        
        self.logger.info("Generated processing statistics", **statistics)
        
        return statistics
