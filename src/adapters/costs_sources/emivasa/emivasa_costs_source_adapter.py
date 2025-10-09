"""
Emivasa costs source adapter.

Fetches water invoices from Emivasa customer portal.
"""

import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ...core.domain.invoice_file import InvoiceFile
from ...core.domain.invoice_metadata import InvoiceMetadata
from ...core.ports.costs_source import CostsSource
from ...infrastructure.browser.selenium_service import SeleniumService
from ...infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class EmivasaCostsSourceAdapter(CostsSource):
    """Adapter for fetching water invoices from Emivasa."""
    
    # Provider-specific configuration
    CONCEPT = "Water"
    TYPE = "Bi-monthly Bill"
    DEDUCTIBLE_PERCENTAGE = 0.0  # 0% deductible - personal expense
    
    # URLs
    LOGIN_URL = "https://www.emivasa.es/VirtualOffice/Login"
    BILLING_URL = "https://www.emivasa.es/VirtualOffice/Secure/Billing"
    
    def __init__(self, username: str, password: str, selenium_service: SeleniumService):
        """Initialize the Emivasa adapter."""
        self.username = username
        self.password = password
        self.selenium_service = selenium_service
        self.logger = logger
        self.driver = None
    
    def get_available_invoices(self, since_date: datetime) -> List[InvoiceMetadata]:
        """
        Get available invoices from Emivasa since the specified date.
        
        Args:
            since_date: Only return invoices from this date onwards
            
        Returns:
            List of invoice metadata objects
        """
        try:
            self.logger.info("Getting available Emivasa invoices", since_date=since_date.isoformat())
            
            # Start browser session
            self.driver = self.selenium_service.start()
            
            # Login to Emivasa
            self._login()
            
            # Navigate to billing page
            self.driver.get(self.BILLING_URL)
            self.selenium_service.wait_for_element(By.CLASS_NAME, "billing", timeout=30)
            
            # Extract invoice metadata from the page
            invoices = self._extract_invoice_metadata(since_date)
            
            self.logger.info("Successfully retrieved Emivasa invoices", 
                           count=len(invoices),
                           since_date=since_date.isoformat())
            
            return invoices
            
        except Exception as e:
            self.logger.error("Failed to get Emivasa invoices", error=str(e))
            raise
        finally:
            if self.driver:
                self.selenium_service.stop()
                self.driver = None
    
    def download_invoice(self, invoice_metadata: InvoiceMetadata) -> InvoiceFile:
        """
        Download a specific invoice file from Emivasa.
        
        Args:
            invoice_metadata: The invoice metadata to download
            
        Returns:
            The downloaded invoice file
        """
        try:
            self.logger.info("Downloading Emivasa invoice", 
                           file_name=invoice_metadata.file_name)
            
            # Start browser session if not already started
            if not self.driver:
                self.driver = self.selenium_service.start()
                self._login()
            
            # Navigate to billing page
            self.driver.get(self.BILLING_URL)
            self.selenium_service.wait_for_element(By.CLASS_NAME, "billing", timeout=30)
            
            # Find and click the download link for this invoice
            download_link = self._find_download_link(invoice_metadata)
            if not download_link:
                raise ValueError(f"Download link not found for invoice {invoice_metadata.file_name}")
            
            # Click download link
            download_link.click()
            
            # Wait for download to complete
            downloaded_file = self.selenium_service.wait_for_download(invoice_metadata.file_name)
            
            # Read the downloaded file
            with open(downloaded_file, 'rb') as f:
                content = f.read()
            
            # Create InvoiceFile object
            invoice_file = InvoiceFile.from_content(content, invoice_metadata.file_name)
            
            self.logger.info("Successfully downloaded Emivasa invoice",
                           file_name=invoice_metadata.file_name,
                           size=len(content))
            
            return invoice_file
            
        except Exception as e:
            self.logger.error("Failed to download Emivasa invoice",
                            file_name=invoice_metadata.file_name,
                            error=str(e))
            raise
    
    def _login(self) -> None:
        """Login to Emivasa customer portal."""
        try:
            self.logger.info("Logging into Emivasa customer portal")
            
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
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .login-btn")
            login_button.click()
            
            # Wait for successful login (redirect to dashboard or billing page)
            self.selenium_service.wait_for_element(By.CLASS_NAME, "dashboard", timeout=30)
            
            self.logger.info("Successfully logged into Emivasa customer portal")
            
        except TimeoutException:
            self.logger.error("Login timeout - check credentials or website availability")
            raise
        except Exception as e:
            self.logger.error("Login failed", error=str(e))
            raise
    
    def _extract_invoice_metadata(self, since_date: datetime) -> List[InvoiceMetadata]:
        """Extract invoice metadata from the billing page."""
        invoices = []
        
        try:
            # Find all invoice rows (adjust selector based on actual HTML structure)
            invoice_rows = self.driver.find_elements(By.CSS_SELECTOR, ".invoice-row, .factura-row, tr[data-invoice], .billing-item, .invoice-item")
            
            for row in invoice_rows:
                try:
                    # Extract invoice data from row
                    invoice_data = self._parse_invoice_row(row)
                    
                    if invoice_data and invoice_data['date'] >= since_date:
                        # Create InvoiceMetadata
                        metadata = InvoiceMetadata(
                            invoice_date=invoice_data['date'],
                            concept=self.CONCEPT,
                            type=self.TYPE,
                            cost_euros=invoice_data['amount'],
                            iva_euros=invoice_data['iva'],
                            deductible_percentage=self.DEDUCTIBLE_PERCENTAGE,
                            file_name=invoice_data['filename']
                        )
                        invoices.append(metadata)
                        
                except Exception as e:
                    self.logger.warning("Failed to parse invoice row", error=str(e))
                    continue
            
            # If no specific rows found, try alternative selectors
            if not invoices:
                invoices = self._extract_invoices_alternative_method(since_date)
            
        except Exception as e:
            self.logger.error("Failed to extract invoice metadata", error=str(e))
            raise
        
        return invoices
    
    def _parse_invoice_row(self, row) -> Optional[dict]:
        """Parse a single invoice row to extract metadata."""
        try:
            # Extract date (adjust selectors based on actual HTML)
            date_element = row.find_element(By.CSS_SELECTOR, ".date, .fecha, .invoice-date, .billing-date, td:nth-child(1)")
            date_text = date_element.text.strip()
            invoice_date = self._parse_date(date_text)
            
            # Extract amount (adjust selectors based on actual HTML)
            amount_element = row.find_element(By.CSS_SELECTOR, ".amount, .importe, .total, .billing-amount, td:nth-child(2)")
            amount_text = amount_element.text.strip()
            amount = self._parse_amount(amount_text)
            
            # Extract IVA (VAT) - might be separate or calculated
            try:
                iva_element = row.find_element(By.CSS_SELECTOR, ".iva, .vat, .tax, .billing-tax, td:nth-child(3)")
                iva_text = iva_element.text.strip()
                iva = self._parse_amount(iva_text)
            except NoSuchElementException:
                # If no separate IVA field, calculate it (assuming 21% VAT)
                iva = amount * Decimal("0.21")
            
            # Generate filename
            filename = f"emivasa_{invoice_date.strftime('%Y%m')}_{amount}.pdf"
            
            return {
                'date': invoice_date,
                'amount': amount,
                'iva': iva,
                'filename': filename
            }
            
        except Exception as e:
            self.logger.warning("Failed to parse invoice row", error=str(e))
            return None
    
    def _extract_invoices_alternative_method(self, since_date: datetime) -> List[InvoiceMetadata]:
        """Alternative method to extract invoices if primary method fails."""
        invoices = []
        
        try:
            # Look for any links that might be invoices
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='factura'], a[href*='invoice'], a[href*='.pdf'], a[href*='download'], a[href*='billing']")
            
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
                        
                        if invoice_date >= since_date:
                            # Create basic metadata (amounts will be extracted from PDF later)
                            metadata = InvoiceMetadata(
                                invoice_date=invoice_date,
                                concept=self.CONCEPT,
                                type=self.TYPE,
                                cost_euros=Decimal("0.00"),  # Will be extracted from PDF
                                iva_euros=Decimal("0.00"),   # Will be extracted from PDF
                                deductible_percentage=self.DEDUCTIBLE_PERCENTAGE,
                                file_name=f"emivasa_{invoice_date.strftime('%Y%m%d')}.pdf"
                            )
                            invoices.append(metadata)
                            
                except Exception as e:
                    self.logger.warning("Failed to parse alternative invoice link", error=str(e))
                    continue
                    
        except Exception as e:
            self.logger.error("Alternative invoice extraction failed", error=str(e))
        
        return invoices
    
    def _find_download_link(self, invoice_metadata: InvoiceMetadata):
        """Find the download link for a specific invoice."""
        try:
            # Look for download links that match the invoice
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='download'], a[href*='.pdf'], button[data-download], .download-btn, .billing-download")
            
            for link in links:
                link_text = link.text.strip().lower()
                href = link.get_attribute('href', '').lower()
                
                # Check if this link matches our invoice
                if (invoice_metadata.file_name.lower() in link_text or 
                    invoice_metadata.file_name.lower() in href or
                    str(invoice_metadata.invoice_date.month) in link_text):
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
