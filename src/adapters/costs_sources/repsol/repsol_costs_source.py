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
            facturas_link = self.browser.wait_for_element(By.LINK_TEXT, "Facturas", timeout=30)
            facturas_link.click()
            
            # Wait for the invoices page to load
            self.browser.wait_for_element(By.TAG_NAME, "body", timeout=30)
            time.sleep(2)  # Give the page time to load completely
            
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
            download_link = metadata.get('download_element')
            if not download_link:
                # Fallback to the old method
                download_link = self._find_download_link_by_metadata(metadata)
                if not download_link:
                    raise ValueError(f"Download link not found for invoice {metadata['filename']}")
            
            # Click download link
            download_link.click()
            
            # Wait a moment for the download to start
            time.sleep(1)
            
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
            # Log current page for debugging
            self.logger.debug("Current page URL", url=self.browser.driver.current_url)
            
            # Find all invoice rows (adjust selector based on actual HTML structure)
            invoice_rows = self.browser.driver.find_elements(By.CSS_SELECTOR, ".factura-row, .invoice-row, tr[data-invoice]")
            self.logger.debug("Found invoice rows with primary selectors", count=len(invoice_rows))
            
            # Look for table rows or list items that might contain invoice data
            table_rows = self.browser.driver.find_elements(By.CSS_SELECTOR, "tbody tr, tbody td, .list-item, [role='row']")
            self.logger.debug("Found table rows/list items", count=len(table_rows))
            
            for row in invoice_rows:
                try:
                    # Extract invoice data from row
                    invoice_data = self._parse_invoice_row(row)
                    
                    if invoice_data:
                        invoices.append(invoice_data)
                        
                except Exception as e:
                    self.logger.warning("Failed to parse invoice row", error=str(e))
                    continue
            
            # If no specific rows found, try table rows
            if not invoices and table_rows:
                self.logger.debug("No invoices found with primary method, trying table rows")
                for row in table_rows:
                    try:
                        # Only parse rows that look like complete invoice entries
                        row_text = row.text.strip()
                        if (len(row_text) > 50 and 
                            ('€' in row_text or 'EUR' in row_text) and 
                            ('ago' in row_text or 'sep' in row_text or 'jul' in row_text or 
                             'jun' in row_text or 'may' in row_text or 'abr' in row_text or
                             'mar' in row_text or 'feb' in row_text or 'ene' in row_text or
                             'dic' in row_text or 'nov' in row_text or 'oct' in row_text)):
                            invoice_data = self._parse_invoice_row(row)
                            if invoice_data:
                                # Find the download element within this row
                                download_element = self._find_download_element_in_row(row)
                                invoice_data['download_element'] = download_element
                                invoices.append(invoice_data)
                    except Exception as e:
                        self.logger.warning("Failed to parse table row", error=str(e))
                        continue
            
            # If still no invoices found, try alternative selectors
            if not invoices:
                self.logger.debug("No invoices found with table rows, trying alternative")
                invoices = self._extract_invoices_alternative_method()
            
        except Exception as e:
            self.logger.error("Failed to extract invoice metadata", error=str(e))
            raise
        
        return invoices
    
    def _parse_invoice_row(self, row: WebElement) -> Optional[Dict[str, Any]]:
        """Parse a single invoice row to extract metadata."""
        try:
            row_text = row.text.strip()
            
            # Skip empty rows or rows that don't look like invoices
            if not row_text or len(row_text) < 10:
                return None
            
            # Look for date patterns in the row text
            # First try Spanish abbreviated month format: "26 ago - 21 sep"
            spanish_months = {
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }
            
            date_match = re.search(r'(\d{1,2})\s+(\w{3})\s*-\s*(\d{1,2})\s+(\w{3})', row_text)
            if date_match:
                # Use the end date (second date) as the invoice date
                day, month_abbr, end_day, end_month_abbr = date_match.groups()
                month = spanish_months.get(end_month_abbr.lower())
                if month:
                    # Assume current year for now
                    current_year = datetime.now().year
                    invoice_date = datetime(current_year, month, int(end_day))
                else:
                    self.logger.debug("Unknown Spanish month abbreviation", month=end_month_abbr)
                    return None
            else:
                # Try standard date formats
                date_match = re.search(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})', row_text)
                if not date_match:
                    # Try alternative date formats
                    date_match = re.search(r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})', row_text)
                
                if not date_match:
                    return None
                
                # Parse the date
                if len(date_match.group(1)) == 4:  # YYYY/MM/DD format
                    year, month, day = date_match.groups()
                else:  # DD/MM/YYYY format
                    day, month, year = date_match.groups()
                
                invoice_date = datetime(int(year), int(month), int(day))
            
            # Look for amount patterns in the row text
            amount_match = re.search(r'(\d+[.,]\d{2})\s*€', row_text)
            if amount_match:
                amount = self._parse_amount(amount_match.group(1))
            else:
                # Try to find any number that looks like an amount
                amount_match = re.search(r'(\d+[.,]\d{2})', row_text)
                if amount_match:
                    amount = self._parse_amount(amount_match.group(1))
                else:
                    amount = Decimal("0.00")
            
            # Calculate IVA (21% of amount, typical Spanish VAT rate)
            iva = amount * Decimal("0.21")
            
            # Generate filename
            filename = f"repsol_{invoice_date.strftime('%Y%m')}_{amount}.pdf"
            
            invoice_data = {
                'date': invoice_date,
                'amount': amount,
                'iva': iva,
                'filename': filename
            }
            
            return invoice_data
            
        except Exception as e:
            self.logger.warning("Failed to parse invoice row", error=str(e))
            return None
    
    def _extract_invoices_alternative_method(self) -> List[Dict[str, Any]]:
        """Alternative method to extract invoices if primary method fails."""
        invoices = []
        
        try:
            # Look for any links that might be invoices
            links = self.browser.driver.find_elements(By.CSS_SELECTOR, "a[href*='factura'], a[href*='invoice'], a[href*='.pdf']")
            self.logger.debug("Found potential invoice links", count=len(links))
            
            # Also try to find any clickable elements that might be invoices
            buttons = self.browser.driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
            self.logger.debug("Found buttons", count=len(buttons))
            
            # Look for any elements with text that might indicate invoices
            all_elements = self.browser.driver.find_elements(By.XPATH, "//*[contains(text(), 'factura') or contains(text(), 'Factura') or contains(text(), 'invoice') or contains(text(), 'Invoice')]")
            self.logger.debug("Found elements with invoice text", count=len(all_elements))
            
            for element in all_elements[:5]:  # Log first 5 elements for debugging
                self.logger.debug("Element with invoice text", 
                                tag=element.tag_name, 
                                text=element.text[:100], 
                                class_name=element.get_attribute('class'))
            
            for link in links:
                try:
                    # Try to extract date and amount from link text or nearby elements
                    link_text = link.text.strip()
                    href = link.get_attribute('href')
                    
                    self.logger.debug("Processing potential invoice link", 
                                    text=link_text, 
                                    href=href)
                    
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
                        self.logger.debug("Created invoice from link", invoice_data=invoice_data)
                            
                except Exception as e:
                    self.logger.warning("Failed to parse alternative invoice link", error=str(e))
                    continue
                    
        except Exception as e:
            self.logger.error("Alternative invoice extraction failed", error=str(e))
        
        return invoices
    
    def _find_download_element_in_row(self, row: WebElement) -> Optional[WebElement]:
        """Find the download element within a specific invoice row."""
        try:
            # Look for elements with "Descargar" text within this row
            download_elements = row.find_elements(By.XPATH, ".//*[contains(text(), 'Descargar') or contains(text(), 'descargar')]")
            
            if download_elements:
                return download_elements[0]  # Return the first one found
            
            # Also look for clickable elements within the row
            clickable_elements = row.find_elements(By.CSS_SELECTOR, "button, a, [role='button'], [onclick]")
            
            for element in clickable_elements:
                element_text = element.text.strip().lower()
                if 'descargar' in element_text:
                    return element
            
            return None
            
        except Exception as e:
            self.logger.warning("Error finding download element in row", error=str(e))
            return None
    
    def _find_download_link_by_metadata(self, metadata: Dict[str, Any]) -> Optional[WebElement]:
        """Find the download link for a specific invoice."""
        try:
            # Look for download links that match the invoice
            # First try to find "Descargar" buttons/links
            download_elements = self.browser.driver.find_elements(By.XPATH, "//*[contains(text(), 'Descargar') or contains(text(), 'descargar')]")
            
            # Also look for traditional download links
            links = self.browser.driver.find_elements(By.CSS_SELECTOR, "a[href*='download'], a[href*='.pdf'], button[data-download]")
            
            # Combine all potential download elements
            all_download_elements = download_elements + links
            
            for element in all_download_elements:
                try:
                    element_text = element.text.strip().lower()
                    
                    # Check if this element matches our invoice
                    # For now, just return the first "Descargar" element we find
                    if 'descargar' in element_text:
                        return element
                        
                except Exception as e:
                    self.logger.warning("Error checking download element", error=str(e))
                    continue
            
            # If no specific link found, return the first download link
            if all_download_elements:
                return all_download_elements[0]
                
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
            
            # Check for any PDF files that might be the download
            pdf_files = list(download_dir.glob("*.pdf"))
            
            if file_path.exists() and not crdownload_path.exists():
                return file_path
            
            # If we find any PDF file, it might be our download with a different name
            if pdf_files and not any(f.name == filename for f in pdf_files):
                # Check if any PDF was created recently (within last 10 seconds)
                recent_pdfs = [f for f in pdf_files if time.time() - f.stat().st_mtime < 10]
                if recent_pdfs:
                    return recent_pdfs[0]
            
            time.sleep(0.5)
        
        raise TimeoutError(f"Download timeout: {filename} not found after {timeout} seconds")
