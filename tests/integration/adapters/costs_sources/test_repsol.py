#!/usr/bin/env python3
"""
Test script for Repsol workflow.

This script tests the Repsol costs source adapter to download the invoice from September 24th.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

# Import with proper path handling
from src.adapters.costs_sources.repsol.repsol_costs_source_adapter import RepsolCostsSourceAdapter
from src.infrastructure.browser.selenium_service import SeleniumService
from src.infrastructure.logging.logger import configure_logging, get_logger

# Load environment variables
load_dotenv()

# Configure logging
configure_logging()
logger = get_logger(__name__)


def test_repsol_workflow():
    """Test the Repsol workflow to download the September 24th invoice."""
    try:
        logger.info("Starting Repsol workflow test")
        
        # Get credentials from environment
        username = os.getenv("REPSOL_USERNAME")
        password = os.getenv("REPSOL_PASSWORD")
        
        if not username or not password:
            logger.error("REPSOL_USERNAME and REPSOL_PASSWORD must be set in environment")
            return False
        
        logger.info("Credentials loaded", username=username)
        
        # Initialize services
        selenium_service = SeleniumService()
        adapter = RepsolCostsSourceAdapter(username, password, selenium_service)
        
        # Set target date (September 24th, 2024)
        target_date = datetime(2024, 9, 24)
        since_date = target_date - timedelta(days=30)  # Look back 30 days
        
        logger.info("Testing Repsol adapter", target_date=target_date.isoformat())
        
        # Test getting available invoices
        logger.info("Getting available invoices...")
        invoices = adapter.get_available_invoices(since_date)
        
        logger.info("Found invoices", count=len(invoices))
        
        # Find the September 24th invoice
        target_invoice = None
        for invoice in invoices:
            logger.info("Found invoice", 
                       date=invoice.invoice_date.isoformat(),
                       concept=invoice.concept,
                       amount=float(invoice.cost_euros))
            
            if invoice.invoice_date.date() == target_date.date():
                target_invoice = invoice
                logger.info("Found target invoice!", file_name=invoice.file_name)
                break
        
        if not target_invoice:
            logger.warning("Target invoice not found", target_date=target_date.isoformat())
            logger.info("Available invoice dates:")
            for invoice in invoices:
                logger.info("  - " + invoice.invoice_date.isoformat())
            return False
        
        # Test downloading the invoice
        logger.info("Downloading target invoice...")
        invoice_file = adapter.download_invoice(target_invoice)
        
        logger.info("Invoice downloaded successfully!",
                   file_name=invoice_file.file_name,
                   size=invoice_file.size,
                   hash=invoice_file.hash_md5)
        
        # Save the file for inspection
        output_path = Path("downloaded_invoice.pdf")
        with open(output_path, "wb") as f:
            f.write(invoice_file.content)
        
        logger.info("Invoice saved to", path=str(output_path))
        
        return True
        
    except Exception as e:
        logger.error("Repsol workflow test failed", error=str(e), exc_info=True)
        return False


def main():
    """Main entry point."""
    print("🔍 Testing Repsol Workflow")
    print("=" * 40)
    
    success = test_repsol_workflow()
    
    if success:
        print("✅ Repsol workflow test completed successfully!")
        print("📄 Invoice downloaded to: downloaded_invoice.pdf")
    else:
        print("❌ Repsol workflow test failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
