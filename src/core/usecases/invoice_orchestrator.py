"""
Invoice orchestrator use case.

Main business logic that coordinates the invoice processing workflow.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..domain.archive_result import ArchiveResult
from ..domain.invoice_file import InvoiceFile
from ..domain.invoice_metadata import InvoiceMetadata
from ..domain.registered_invoice import RegisteredInvoice
from ..ports.costs_registry import CostsRegistry
from ..ports.costs_source import CostsSource
from ..ports.invoice_archive import InvoiceArchive
from .file_processing_service import FileProcessingService
from .idempotency_service import IdempotencyService
from ...infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class InvoiceOrchestrator:
    """Main orchestrator for the invoice processing workflow."""
    
    def __init__(
        self,
        costs_sources: List[CostsSource],
        invoice_archive: InvoiceArchive,
        costs_registry: CostsRegistry,
        file_processing_service: FileProcessingService,
        idempotency_service: IdempotencyService
    ):
        """Initialize the invoice orchestrator."""
        self.costs_sources = costs_sources
        self.invoice_archive = invoice_archive
        self.costs_registry = costs_registry
        self.file_processing_service = file_processing_service
        self.idempotency_service = idempotency_service
        self.logger = logger
    
    def process_invoices(self, since_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Process invoices from all configured sources.
        
        Args:
            since_date: Only process invoices from this date onwards
            
        Returns:
            Dictionary with processing results and statistics
        """
        start_time = datetime.now()
        lookback_date = since_date or (datetime.now() - timedelta(days=90))
        
        self.logger.info("Starting invoice processing", 
                        since_date=lookback_date.isoformat(),
                        sources_count=len(self.costs_sources))
        
        results = {
            "start_time": start_time.isoformat(),
            "sources_processed": 0,
            "total_invoices_found": 0,
            "total_invoices_processed": 0,
            "total_invoices_skipped": 0,
            "total_invoices_failed": 0,
            "source_results": [],
            "errors": []
        }
        
        for costs_source in self.costs_sources:
            try:
                source_result = self._process_source(costs_source, lookback_date)
                results["source_results"].append(source_result)
                results["sources_processed"] += 1
                results["total_invoices_found"] += source_result["invoices_found"]
                results["total_invoices_processed"] += source_result["invoices_processed"]
                results["total_invoices_skipped"] += source_result["invoices_skipped"]
                results["total_invoices_failed"] += source_result["invoices_failed"]
                
            except Exception as e:
                error_msg = f"Failed to process source {type(costs_source).__name__}: {str(e)}"
                self.logger.error("Source processing failed", 
                                source=type(costs_source).__name__,
                                error=str(e))
                results["errors"].append(error_msg)
        
        end_time = datetime.now()
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # Generate final statistics
        results["statistics"] = self.idempotency_service.get_processing_statistics(lookback_date)
        
        self.logger.info("Invoice processing completed",
                        duration_seconds=results["duration_seconds"],
                        total_processed=results["total_invoices_processed"],
                        total_failed=results["total_invoices_failed"],
                        success_rate=self._calculate_success_rate(results))
        
        return results
    
    def _process_source(self, costs_source: CostsSource, since_date: datetime) -> Dict[str, Any]:
        """Process invoices from a single source."""
        source_name = type(costs_source).__name__
        
        self.logger.info("Processing source", source=source_name)
        
        source_result = {
            "source": source_name,
            "invoices_found": 0,
            "invoices_processed": 0,
            "invoices_skipped": 0,
            "invoices_failed": 0,
            "errors": []
        }
        
        try:
            # Get available invoices from the source
            available_invoices = costs_source.get_available_invoices(since_date)
            source_result["invoices_found"] = len(available_invoices)
            
            self.logger.info("Found available invoices", 
                           source=source_name,
                           count=len(available_invoices))
            
            # Filter out already processed invoices
            new_invoices = self.idempotency_service.filter_new_invoices(available_invoices, since_date)
            
            self.logger.info("Filtered new invoices", 
                           source=source_name,
                           new_count=len(new_invoices),
                           skipped_count=len(available_invoices) - len(new_invoices))
            
            # Process each new invoice
            for invoice_metadata in new_invoices:
                try:
                    success = self._process_single_invoice(costs_source, invoice_metadata)
                    if success:
                        source_result["invoices_processed"] += 1
                    else:
                        source_result["invoices_failed"] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to process invoice {invoice_metadata.file_name}: {str(e)}"
                    self.logger.error("Invoice processing failed",
                                    source=source_name,
                                    file_name=invoice_metadata.file_name,
                                    error=str(e))
                    source_result["errors"].append(error_msg)
                    source_result["invoices_failed"] += 1
            
            source_result["invoices_skipped"] = len(available_invoices) - len(new_invoices)
            
        except Exception as e:
            error_msg = f"Failed to get available invoices from {source_name}: {str(e)}"
            self.logger.error("Source invoice retrieval failed",
                            source=source_name,
                            error=str(e))
            source_result["errors"].append(error_msg)
        
        self.logger.info("Source processing completed",
                        source=source_name,
                        processed=source_result["invoices_processed"],
                        failed=source_result["invoices_failed"],
                        skipped=source_result["invoices_skipped"])
        
        return source_result
    
    def _process_single_invoice(self, costs_source: CostsSource, invoice_metadata: InvoiceMetadata) -> bool:
        """Process a single invoice through the complete workflow."""
        try:
            # Download the invoice file
            self.logger.debug("Downloading invoice file",
                            file_name=invoice_metadata.file_name)
            
            invoice_file = costs_source.download_invoice(invoice_metadata)
            
            # Validate the PDF file
            if not self.file_processing_service.validate_pdf_file(invoice_file):
                self.logger.error("Invalid PDF file",
                                file_name=invoice_metadata.file_name)
                return False
            
            # Extract metadata from the PDF (this will override the metadata from the source)
            extracted_metadata = self.file_processing_service.extract_metadata_from_pdf(
                invoice_file, 
                invoice_metadata.concept,
                invoice_metadata.type,
                invoice_metadata.deductible_percentage
            )
            
            # Archive the invoice file
            self.logger.debug("Archiving invoice file",
                            file_name=invoice_metadata.file_name)
            
            archive_result = self.invoice_archive.archive_invoice(invoice_file, extracted_metadata)
            
            if not archive_result.success:
                self.logger.error("Failed to archive invoice",
                                file_name=invoice_metadata.file_name,
                                error=archive_result.error_message)
                return False
            
            # Register the invoice
            self.logger.debug("Registering invoice",
                            file_name=invoice_metadata.file_name)
            
            success = self.costs_registry.register_invoice(extracted_metadata, [archive_result])
            
            if success:
                self.logger.info("Successfully processed invoice",
                               file_name=invoice_metadata.file_name,
                               invoice_date=extracted_metadata.invoice_date.isoformat(),
                               cost_euros=float(extracted_metadata.cost_euros))
            else:
                self.logger.error("Failed to register invoice",
                                file_name=invoice_metadata.file_name)
            
            return success
            
        except Exception as e:
            self.logger.error("Invoice processing failed",
                            file_name=invoice_metadata.file_name,
                            error=str(e))
            return False
    
    def _calculate_success_rate(self, results: Dict[str, Any]) -> float:
        """Calculate the overall success rate."""
        total_attempted = results["total_invoices_processed"] + results["total_invoices_failed"]
        if total_attempted == 0:
            return 0.0
        
        return (results["total_invoices_processed"] / total_attempted) * 100
