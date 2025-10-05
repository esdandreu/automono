"""
Main application entry point for invoice automation.

This is the main entry point that orchestrates the entire invoice processing workflow.
"""

import sys
from datetime import datetime, timedelta
from typing import List

from core.usecases.file_processing_service import FileProcessingService
from core.usecases.idempotency_service import IdempotencyService
from core.usecases.invoice_orchestrator import InvoiceOrchestrator
from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import configure_logging, get_logger

# Import adapters (these will be implemented next)
# from adapters.costs_sources.repsol.repsol_costs_source_adapter import RepsolCostsSourceAdapter
# from adapters.costs_sources.digi.digi_costs_source_adapter import DigiCostsSourceAdapter
# from adapters.costs_sources.emivasa.emivasa_costs_source_adapter import EmivasaCostsSourceAdapter
# from adapters.archives.multiplexer.multiplexer_adapter import MultiplexerArchiveAdapter
# from adapters.registry.google_sheets.google_sheets_costs_registry_adapter import GoogleSheetsCostsRegistryAdapter


def main():
    """Main application entry point."""
    # Configure logging
    configure_logging()
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting invoice automation system")
        
        # Load settings
        settings = get_settings()
        logger.info("Configuration loaded successfully")
        
        # Initialize services
        file_processing_service = FileProcessingService()
        logger.info("File processing service initialized")
        
        # TODO: Initialize adapters when they are implemented
        # costs_sources = [
        #     RepsolCostsSourceAdapter(settings.repsol_username, settings.repsol_password),
        #     DigiCostsSourceAdapter(settings.digi_username, settings.digi_password),
        #     EmivasaCostsSourceAdapter(settings.emivasa_username, settings.emivasa_password),
        # ]
        # 
        # invoice_archive = MultiplexerArchiveAdapter(
        #     google_drive_adapter=GoogleDriveArchiveAdapter(settings.google_credentials_json, settings.google_drive_folder_id),
        #     onedrive_adapter=OneDriveArchiveAdapter(settings.microsoft_client_id, settings.microsoft_client_secret, settings.microsoft_tenant_id, settings.onedrive_folder_id)
        # )
        # 
        # costs_registry = GoogleSheetsCostsRegistryAdapter(settings.google_credentials_json, settings.google_sheets_id)
        
        # For now, create empty lists/None to allow the system to start
        costs_sources: List = []
        invoice_archive = None
        costs_registry = None
        
        # Initialize idempotency service
        if costs_registry:
            idempotency_service = IdempotencyService(costs_registry)
        else:
            logger.warning("Costs registry not available, idempotency service will not function properly")
            idempotency_service = None
        
        # Initialize orchestrator
        if costs_sources and invoice_archive and costs_registry and idempotency_service:
            orchestrator = InvoiceOrchestrator(
                costs_sources=costs_sources,
                invoice_archive=invoice_archive,
                costs_registry=costs_registry,
                file_processing_service=file_processing_service,
                idempotency_service=idempotency_service
            )
            
            # Process invoices
            lookback_days = settings.invoice_lookback_days
            since_date = datetime.now() - timedelta(days=lookback_days)
            
            logger.info("Starting invoice processing", 
                       lookback_days=lookback_days,
                       since_date=since_date.isoformat())
            
            results = orchestrator.process_invoices(since_date)
            
            # Log results
            logger.info("Invoice processing completed",
                       duration_seconds=results["duration_seconds"],
                       total_processed=results["total_invoices_processed"],
                       total_failed=results["total_invoices_failed"],
                       success_rate=results.get("statistics", {}).get("success_rate", 0))
            
            # Print summary
            print("\n" + "="*50)
            print("INVOICE PROCESSING SUMMARY")
            print("="*50)
            print(f"Duration: {results['duration_seconds']:.2f} seconds")
            print(f"Sources processed: {results['sources_processed']}")
            print(f"Total invoices found: {results['total_invoices_found']}")
            print(f"Total invoices processed: {results['total_invoices_processed']}")
            print(f"Total invoices failed: {results['total_invoices_failed']}")
            print(f"Total invoices skipped: {results['total_invoices_skipped']}")
            
            if results["errors"]:
                print(f"\nErrors encountered: {len(results['errors'])}")
                for error in results["errors"]:
                    print(f"  - {error}")
            
            print("="*50)
            
        else:
            logger.warning("Not all required services are available. Adapters need to be implemented.")
            print("\n" + "="*50)
            print("SYSTEM NOT FULLY CONFIGURED")
            print("="*50)
            print("The core system is ready, but adapters need to be implemented:")
            print("- Costs source adapters (Repsol, Digi, Emivasa)")
            print("- Archive adapters (Google Drive, OneDrive)")
            print("- Registry adapter (Google Sheets)")
            print("="*50)
        
        logger.info("Invoice automation system completed successfully")
        return 0
        
    except Exception as e:
        logger.error("Invoice automation system failed", error=str(e), exc_info=True)
        print(f"\nERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
