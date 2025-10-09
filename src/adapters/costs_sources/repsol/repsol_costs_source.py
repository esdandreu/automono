"""
Repsol costs source adapter.

Fetches electricity invoices from Repsol customer portal.
"""

from abc import abstractmethod
import re
import time
from datetime import datetime
from decimal import Decimal
from typing import Iterator, List, Optional, Dict, Any, Final, Protocol

from src.core.domain.invoice import Invoice
from src.core.ports.costs_source import CostsSource
from src.core.ports.logger import Logger
from src.core.ports.browser import Browser, By, WebElement


class RepsolConfig(Protocol):
    @property
    @abstractmethod
    def repsol_username(self) -> str:
        """Repsol username."""
        pass
    
    @property
    @abstractmethod
    def repsol_password(self) -> str:
        """Repsol password."""
        pass

class RepsolCostsSource(CostsSource):
    """Adapter for fetching electricity invoices from Repsol."""
    
    # Provider-specific configuration
    CONCEPT: Final[str] = "Electricity"
    TYPE: Final[str] = "Monthly Bill"
    DEDUCTIBLE_PERCENTAGE: Final[float] = 1.0  # 100% deductible for business
    
    # URLs
    INVOICES_URL: Final[str] = "https://areacliente.repsol.es/mis-facturas"
    
    def __init__(self, config: RepsolConfig, browser: Browser, logger: Logger):
        """Initialize the Repsol adapter."""
        self.username = config.repsol_username
        self.password = config.repsol_password
        self.browser = browser
        self.logger = logger
    
    def __iter__(self) -> Iterator[Invoice]:
        """
        Iterate over Repsol invoices from newest to oldest.
        
        Yields:
            Invoice objects with complete metadata and file content
        """
        self.browser.start()
        try:
            self.logger.info("Finding Repsol invoices")
            
            # Login to Repsol
            self.browser.driver.get(self.INVOICES_URL)
            self._login()

            # Navigate to invoices page
            self.browser.wait_for_element(By.LINK_TEXT, "Facturas", timeout=30).click()
            
            # Get invoice metadata and download each one
            invoice_metadata_list = self._extract_invoice_metadata()
            self.logger.info("Found Repsol invoices", count=len(invoice_metadata_list))
            
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
                    
                    self.logger.info("Successfully processed Repsol invoice",
                                   file_name=metadata['filename'],
                                   date=metadata['date'].isoformat())
                    
                    yield invoice
                    
                except Exception as e:
                    self.logger.error("Failed to process Repsol invoice",
                                    file_name=metadata.get('filename', 'unknown'),
                                    error=str(e))
                    continue
        finally:
            self.browser.stop()
     
    def _login(self) -> None:
        """Login to Repsol customer portal."""
        self.logger.info("Logging into Repsol customer portal")
        # Handle cookie policy if present
        self._accept_cookie_policy(timeout=10)
        # Fill username
        username_field = self.browser.wait_for_element(By.ID, "mail", timeout=30)
        username_field.clear()
        username_field.send_keys(self.username)
        # Fill password
        password_field = self.browser.wait_for_element(By.ID, "pass", timeout=30)
        password_field.clear()
        password_field.send_keys(self.password)
        # Submit login form
        login_button = self.browser.wait_for_clickable(By.CSS_SELECTOR, "button[type='submit']", timeout=30)
        login_button.click()
        self.logger.info("Successfully logged into Repsol customer portal")
    
    def _download_invoice_file(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Download a specific invoice file and return file data."""
        try:
            self.logger.info("Downloading Repsol invoice file", 
                           file_name=metadata['filename'])
            
            # Find and click the download link for this invoice
            download_link = self._find_download_link_by_metadata(metadata)
            if not download_link:
                raise ValueError(f"Download link not found for invoice {metadata['filename']}")
            
            # Click download link
            download_link.click()
            
            # Wait for download to complete
            downloaded_file = self._wait_for_download(metadata['filename'])
            
            # Read the downloaded file
            with open(downloaded_file, 'rb') as f:
                content = f.read()
            
            # Calculate hashes
            import hashlib
            hash_md5 = hashlib.md5(content).hexdigest()
            hash_sha256 = hashlib.sha256(content).hexdigest()
            
            self.logger.info("Successfully downloaded Repsol invoice file",
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
            self.logger.error("Failed to download Repsol invoice file",
                            file_name=metadata.get('filename', 'unknown'),
                            error=str(e))
            raise
      
    
    def _extract_invoice_metadata(self) -> List[Dict[str, Any]]:
        """Extract invoice metadata from the invoices page."""
        invoices = []
        
        try:
            # Find all invoice rows (adjust selector based on actual HTML structure)
            invoice_rows = self.browser.driver.find_elements(By.CSS_SELECTOR, ".factura-row, .invoice-row, tr[data-invoice]")
            
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
    
    def _parse_invoice_row(self, row: WebElement) -> Optional[Dict[str, Any]]:
        """Parse a single invoice row to extract metadata."""
        try:
            # Extract date (adjust selectors based on actual HTML)
            date_element = row.find_element(By.CSS_SELECTOR, ".date, .fecha, td:nth-child(1)")
            date_text = date_element.text.strip()
            invoice_date = self._parse_date(date_text)
            
            # Extract amount (adjust selectors based on actual HTML)
            amount_element = row.find_element(By.CSS_SELECTOR, ".amount, .importe, td:nth-child(2)")
            amount_text = amount_element.text.strip()
            amount = self._parse_amount(amount_text)
            
            # Extract IVA (VAT) - might be separate or calculated
            iva_element = row.find_element(By.CSS_SELECTOR, ".iva, .vat, td:nth-child(3)")
            iva_text = iva_element.text.strip()
            iva = self._parse_amount(iva_text)
            
            # Generate filename
            filename = f"repsol_{invoice_date.strftime('%Y%m')}_{amount}.pdf"
            
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
            links = self.browser.driver.find_elements(By.CSS_SELECTOR, "a[href*='factura'], a[href*='invoice'], a[href*='.pdf']")
            
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
                            'filename': f"repsol_{invoice_date.strftime('%Y%m%d')}.pdf"
                        }
                        invoices.append(invoice_data)
                            
                except Exception as e:
                    self.logger.warning("Failed to parse alternative invoice link", error=str(e))
                    continue
                    
        except Exception as e:
            self.logger.error("Alternative invoice extraction failed", error=str(e))
        
        return invoices
    
    def _find_download_link_by_metadata(self, metadata: Dict[str, Any]) -> Optional[WebElement]:
        """Find the download link for a specific invoice."""
        try:
            # Look for download links that match the invoice
            links = self.browser.driver.find_elements(By.CSS_SELECTOR, "a[href*='download'], a[href*='.pdf'], button[data-download]")
            
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
        except (ValueError, TypeError):
            return Decimal("0.00")
    
    def _accept_cookie_policy(self, timeout: int = 10) -> bool:
        """Accept cookie policy if present. Returns True if accepted, False if not found."""
        # Common cookie policy button selectors
        cookie_selectors = [
            # Generic cookie accept buttons
            "button[id*='accept']",
            "button[class*='accept']",
            "button[id*='cookie']",
            "button[class*='cookie']",
            "button[id*='consent']",
            "button[class*='consent']",
            # Common text-based selectors
            "button:contains('Accept')",
            "button:contains('Aceptar')",
            "button:contains('Accept All')",
            "button:contains('Aceptar todo')",
            "button:contains('Accept Cookies')",
            "button:contains('Aceptar cookies')",
            # Common ID/class patterns
            "#cookie-accept",
            "#accept-cookies",
            "#cookie-consent",
            ".cookie-accept",
            ".accept-cookies",
            ".cookie-consent",
            ".cookie-banner button",
            ".consent-banner button",
            # Repsol-specific selectors (if any)
            "[data-testid*='cookie']",
            "[data-testid*='accept']",
            "[data-testid*='consent']"
        ]
        
        try:
            # Try to find and click cookie accept button
            for selector in cookie_selectors:
                try:
                    element = self.browser.wait_for_element(By.CSS_SELECTOR, selector)
                    self.logger.debug("Accepted cookie policy banner")
                    element.click()
                    time.sleep(0.1)
                    return True
                except Exception:
                    # Continue to next selector if this one doesn't work
                    continue
            else:
                self.logger.debug("No cookie policy banner found")
                return False
        except Exception as e:
            self.logger.warning("Error handling cookie policy", error=str(e))
            return False
    
    def _wait_for_download(self, filename: str, timeout: int = 30):
        """Wait for a file to be downloaded and return its path."""
        download_dir = self.browser.get_download_dir()
        self.logger.debug("Waiting for download", filename=filename, timeout=timeout)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for the file in the download directory
            file_path = download_dir / filename
            
            # Also check for .crdownload files (Chrome download in progress)
            crdownload_path = download_dir / f"{filename}.crdownload"
            
            if file_path.exists() and not crdownload_path.exists():
                self.logger.debug("Download completed", file_path=str(file_path))
                return file_path
            
            time.sleep(0.5)
        
        raise TimeoutError(f"Download timeout: {filename} not found after {timeout} seconds")
