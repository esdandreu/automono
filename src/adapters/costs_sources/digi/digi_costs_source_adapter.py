"""
Digi costs source adapter.

Fetches internet invoices from Digi customer portal.
"""

import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterator, List, Optional, Dict, Any
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ...core.domain.invoice import Invoice
from ...core.ports.costs_source import CostsSource
from ...infrastructure.browser.selenium_service import SeleniumService
from ...infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class DigiCostsSourceAdapter(CostsSource):
    """Adapter for fetching internet invoices from Digi."""
    
    # Provider-specific configuration
    CONCEPT = "Internet"
    TYPE = "Monthly Bill"
    DEDUCTIBLE_PERCENTAGE = 1.0  # 100% deductible for business
    
    # URLs
    LOGIN_URL = "https://midigi.digimobil.es/login"
    INVOICES_URL = "https://midigi.digimobil.es/invoice"
    
    def __init__(self, username: str, password: str, selenium_service: SeleniumService):
        """Initialize the Digi adapter."""
        self.username = username
        self.password = password
        self.selenium_service = selenium_service
        self.logger = logger
        self.driver = None
    
    def __iter__(self) -> Iterator[Invoice]:
        """
        Iterate over Digi invoices from newest to oldest.
        
        Yields:
            Invoice objects with complete metadata and file content
        """
        try:
            self.logger.info("Starting Digi invoice iteration")
            
            # Start browser session
            self.driver = self.selenium_service.start()
            
            # Login to Digi
            self._login()
            
            # Navigate to invoices page
            self.driver.get(self.INVOICES_URL)
            self.selenium_service.wait_for_element(By.CLASS_NAME, "invoices", timeout=30)
            
            # Get invoice metadata and download each one
            invoice_metadata_list = self._extract_invoice_metadata()
            
            for metadata in invoice_metadata_list:
                try:
                    # Download the invoice file
                    invoice_file = self._download_invoice_file(metadata)
                    
                    # Create unified Invoice object
                    invoice = Invoice(
                        # Metadata fields
                        invoice_date=metadata['date'],
                        concept=self.CONCEPT,
                        type=self.TYPE,
                        cost_euros=metadata['amount'],
                        iva_euros=metadata['iva'],
                        deductible_percentage=self.DEDUCTIBLE_PERCENTAGE,
                        file_name=metadata['filename'],
                        # File fields
                        content=invoice_file['content'],
                        content_type=invoice_file['content_type'],
                        size=invoice_file['size'],
                        hash_md5=invoice_file['hash_md5'],
                        hash_sha256=invoice_file['hash_sha256']
                    )
                    
                    self.logger.info("Successfully processed Digi invoice",
                                   file_name=metadata['filename'],
                                   date=metadata['date'].isoformat())
                    
                    yield invoice
                    
                except Exception as e:
                    self.logger.error("Failed to process Digi invoice",
                                    file_name=metadata.get('filename', 'unknown'),
                                    error=str(e))
                    continue
            
        except Exception as e:
            self.logger.error("Failed to iterate Digi invoices", error=str(e))
            raise
        finally:
            if self.driver:
                self.selenium_service.stop()
                self.driver = None
    
    def _download_invoice_file(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Download a specific invoice file and return file data."""
        try:
            self.logger.info("Downloading Digi invoice file", 
                           file_name=metadata['filename'])
            
            # Find and click the download link for this invoice
            download_link = self._find_download_link_by_metadata(metadata)
            if not download_link:
                raise ValueError(f"Download link not found for invoice {metadata['filename']}")
            
            # Click download link
            download_link.click()
            
            # Wait for download to complete
            downloaded_file = self.selenium_service.wait_for_download(metadata['filename'])
            
            # Read the downloaded file
            with open(downloaded_file, 'rb') as f:
                content = f.read()
            
            # Calculate hashes
            import hashlib
            hash_md5 = hashlib.md5(content).hexdigest()
            hash_sha256 = hashlib.sha256(content).hexdigest()
            
            self.logger.info("Successfully downloaded Digi invoice file",
                           file_name=metadata['filename'],
                           size=len(content))
            
            return {
                'content': content,
                'content_type': 'application/pdf',
                'size': len(content),
                'hash_md5': hash_md5,
                'hash_sha256': hash_sha256
            }
            
        except Exception as e:
            self.logger.error("Failed to download Digi invoice file",
                            file_name=metadata.get('filename', 'unknown'),
                            error=str(e))
            raise
    
    def _login(self) -> None:
        """Login to Digi customer portal."""
        try:
            self.logger.info("Logging into Digi customer portal")
            
            # Navigate to login page
            self.driver.get(self.LOGIN_URL)
            
            # Wait for login form
            self.selenium_service.wait_for_element(By.ID, "username", timeout=30)
            
            # Fill username
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Fill password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit login form
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_button.click()
            
            # Wait for successful login (redirect to dashboard or invoices page)
            self.selenium_service.wait_for_element(By.CLASS_NAME, "dashboard", timeout=30)
            
            self.logger.info("Successfully logged into Digi customer portal")
            
        except TimeoutException:
            self.logger.error("Login timeout - check credentials or website availability")
            raise
        except Exception as e:
            self.logger.error("Login failed", error=str(e))
            raise
    
    def _extract_invoice_metadata(self) -> List[Dict[str, Any]]:
        """Extract invoice metadata from the invoices page."""
        invoices = []
        
        try:
            # Find all invoice rows (adjust selector based on actual HTML structure)
            invoice_rows = self.driver.find_elements(By.CSS_SELECTOR, ".invoice-row, .factura-row, tr[data-invoice], .invoice-item")
            
            for row in invoice_rows:
                try:
                    # Extract invoice data from row
                    invoice_data = self._parse_invoice_row(row)
                    
                    if invoice_data:
                        invoices.append(invoice_data)
                        
                except Exception as e:
                    self.logger.warning("Failed to parse invoice row", error=str(e))
                    continue
            
            # If no specific rows found, try alternative selectors
            if not invoices:
                invoices = self._extract_invoices_alternative_method()
            
        except Exception as e:
            self.logger.error("Failed to extract invoice metadata", error=str(e))
            raise
        
        return invoices
    
    def _parse_invoice_row(self, row) -> Optional[dict]:
        """Parse a single invoice row to extract metadata."""
        try:
            # Extract date (adjust selectors based on actual HTML)
            date_element = row.find_element(By.CSS_SELECTOR, ".date, .fecha, .invoice-date, td:nth-child(1)")
            date_text = date_element.text.strip()
            invoice_date = self._parse_date(date_text)
            
            # Extract amount (adjust selectors based on actual HTML)
            amount_element = row.find_element(By.CSS_SELECTOR, ".amount, .importe, .total, td:nth-child(2)")
            amount_text = amount_element.text.strip()
            amount = self._parse_amount(amount_text)
            
            # Extract IVA (VAT) - might be separate or calculated
            try:
                iva_element = row.find_element(By.CSS_SELECTOR, ".iva, .vat, .tax, td:nth-child(3)")
                iva_text = iva_element.text.strip()
                iva = self._parse_amount(iva_text)
            except NoSuchElementException:
                # If no separate IVA field, calculate it (assuming 21% VAT)
                iva = amount * Decimal("0.21")
            
            # Generate filename
            filename = f"digi_{invoice_date.strftime('%Y%m')}_{amount}.pdf"
            
            return {
                'date': invoice_date,
                'amount': amount,
                'iva': iva,
                'filename': filename
            }
            
        except Exception as e:
            self.logger.warning("Failed to parse invoice row", error=str(e))
            return None
    
    def _extract_invoices_alternative_method(self) -> List[Dict[str, Any]]:
        """Alternative method to extract invoices if primary method fails."""
        invoices = []
        
        try:
            # Look for any links that might be invoices
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='factura'], a[href*='invoice'], a[href*='.pdf'], a[href*='download']")
            
            for link in links:
                try:
                    # Try to extract date and amount from link text or nearby elements
                    link_text = link.text.strip()
                    href = link.get_attribute('href')
                    
                    # Parse date from link text or href
                    date_match = re.search(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})', link_text + href)
                    if date_match:
                        day, month, year = date_match.groups()
                        invoice_date = datetime(int(year), int(month), int(day))
                        
                        # Create basic metadata (amounts will be extracted from PDF later)
                        invoice_data = {
                            'date': invoice_date,
                            'amount': Decimal("0.00"),  # Will be extracted from PDF
                            'iva': Decimal("0.00"),   # Will be extracted from PDF
                            'filename': f"digi_{invoice_date.strftime('%Y%m%d')}.pdf"
                        }
                        invoices.append(invoice_data)
                            
                except Exception as e:
                    self.logger.warning("Failed to parse alternative invoice link", error=str(e))
                    continue
                    
        except Exception as e:
            self.logger.error("Alternative invoice extraction failed", error=str(e))
        
        return invoices
    
    def _find_download_link_by_metadata(self, metadata: Dict[str, Any]):
        """Find the download link for a specific invoice."""
        try:
            # Look for download links that match the invoice
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='download'], a[href*='.pdf'], button[data-download], .download-btn")
            
            for link in links:
                link_text = link.text.strip().lower()
                href = link.get_attribute('href', '').lower()
                
                # Check if this link matches our invoice
                if (metadata['filename'].lower() in link_text or 
                    metadata['filename'].lower() in href or
                    str(metadata['date'].month) in link_text):
                    return link
            
            # If no specific link found, return the first download link
            if links:
                return links[0]
                
            return None
            
        except Exception as e:
            self.logger.error("Failed to find download link", error=str(e))
            return None
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse date from text."""
        # Common Spanish date formats
        date_patterns = [
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',  # DD/MM/YYYY
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',  # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                if len(match.groups()) == 3:
                    if len(match.group(1)) == 4:  # YYYY/MM/DD format
                        year, month, day = match.groups()
                    else:  # DD/MM/YYYY format
                        day, month, year = match.groups()
                    
                    return datetime(int(year), int(month), int(day))
        
        raise ValueError(f"Could not parse date from: {date_text}")
    
    def _parse_amount(self, amount_text: str) -> Decimal:
        """Parse amount from text."""
        # Remove currency symbols and clean up
        cleaned = re.sub(r'[€$£]', '', amount_text)
        cleaned = re.sub(r'[^\d,.-]', '', cleaned)
        
        # Replace comma with point for decimal parsing
        cleaned = cleaned.replace(',', '.')
        
        try:
            return Decimal(cleaned)
        except:
            return Decimal("0.00")
