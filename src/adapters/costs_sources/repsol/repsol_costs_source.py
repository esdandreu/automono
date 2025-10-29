"""
Repsol costs source adapter.

Fetches electricity invoices from Repsol customer portal.
"""

import io
import re
import time
from abc import abstractmethod
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterator, Protocol, Final, Optional

import PyPDF2
import pdfplumber

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

    def __init__(
        self,
        config: RepsolConfig,
        browser: Browser,
        logger: Logger,
        artifacts_dir: Optional[str] = None,
    ):
        """Initialize the Repsol adapter."""
        self.username = config.repsol_username
        self.password = config.repsol_password
        self.browser = browser
        self.logger = logger
        self.artifacts_dir = artifacts_dir

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
            facturas_link = self.browser.wait_for_element(
                By.LINK_TEXT, "Facturas", timeout=30
            )
            facturas_link.click()

            # Wait for the invoices page to load - wait for h1 with "Facturas" text
            self.browser.wait_for_element_with_text(
                By.TAG_NAME, "h1", "Facturas", timeout=30
            )

            # Try to download new invoices first
            for file_path in self._download_invoices():
                try:
                    # Extract metadata from the PDF file
                    invoice = self._extract_metadata_from_pdf_file(file_path)

                    # Set the concept, type, and deductible percentage
                    invoice.concept = self.CONCEPT
                    invoice.type = self.TYPE
                    invoice.deductible_percentage = self.DEDUCTIBLE_PERCENTAGE

                    self.logger.info(
                        "Successfully processed Repsol invoice from file",
                        file_name=invoice.file_name,
                        date=(
                            invoice.invoice_date.isoformat()
                            if invoice.invoice_date
                            else "unknown"
                        ),
                        cost_euros=float(invoice.cost_euros),
                        iva_euros=float(invoice.iva_euros),
                    )

                    yield invoice

                except Exception as e:
                    self.logger.error(
                        "Failed to process downloaded invoice file",
                        file_path=str(file_path),
                        error=str(e),
                    )
                    continue
        except Exception as e:
            self.logger.error("Failed to iterate over Repsol invoices", error=str(e))
            raise
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
        login_button = self.browser.wait_for_clickable(
            By.CSS_SELECTOR, "button[type='submit']", timeout=30
        )
        login_button.click()
        self.logger.info("Successfully logged into Repsol customer portal")

    def _get_download_buttons(self) -> list[WebElement]:
        """Get all download buttons."""
        # Wait for "Hogares" label to be present. Meaning that the facturas
        # page is loaded.
        self.browser.wait_for_element_with_text(By.TAG_NAME, "label", "Hogares")
        # Get all buttons.
        all_buttons = self.browser.driver.find_elements(By.CSS_SELECTOR, "button")
        # Filter by text content.
        return [
            button
            for button in all_buttons
            if "Descargar" in button.get_attribute("innerText")
        ]

    def _download_invoices(self) -> Iterator[Path]:
        """Generator that downloads invoice files one by one to the artifacts directory."""
        try:

            # Wait for "Hogares" label to be present

            self.logger.info("Starting to download Repsol invoices")

            len_download_buttons = len(self._get_download_buttons())
            self.logger.info("Found download elements", count=len_download_buttons)

            # Create artifacts directory if it doesn't exist
            if not self.artifacts_dir:
                raise ValueError("Artifacts directory not specified")

            artifacts_path = Path(self.artifacts_dir)
            artifacts_path.mkdir(parents=True, exist_ok=True)

            # Create a subdirectory for Repsol invoices
            repsol_dir = artifacts_path / "repsol"
            repsol_dir.mkdir(exist_ok=True)

            # Download each invoice one by one
            for i in range(len_download_buttons):
                try:
                    download_button = self._get_download_buttons()[i]

                    self.logger.info(
                        "Downloading invoice", index=i + 1, total=len_download_buttons
                    )

                    # Click the download element
                    download_button.click()

                    # Wait a moment for the download to start
                    time.sleep(1)

                    # Wait for download to complete and get the file path
                    downloaded_file = self._wait_for_download(
                        f"repsol_invoice_{i+1}.pdf"
                    )

                    # Move the file to the artifacts directory with a proper name
                    final_path = repsol_dir / f"repsol_invoice_{i+1}.pdf"
                    if downloaded_file != final_path:
                        import shutil

                        shutil.move(str(downloaded_file), str(final_path))

                    self.logger.info(
                        "Successfully downloaded invoice",
                        file_path=str(final_path),
                        index=i + 1,
                    )

                    # Yield the file path immediately
                    yield final_path

                except Exception as e:
                    self.logger.error(
                        "Failed to download invoice", index=i + 1, error=str(e)
                    )
                    continue

        except Exception as e:
            self.logger.error("Failed to download invoices", error=str(e))
            raise

    def _extract_metadata_from_pdf_file(self, file_path: str) -> Invoice:
        """
        Extract metadata from a Repsol PDF invoice file and create an Invoice object.

        Args:
            file_path: Path to the PDF file

        Returns:
            Invoice object with extracted information

        Raises:
            ValueError: If the PDF cannot be processed or metadata cannot be extracted
        """
        try:
            # Read the PDF file
            with open(file_path, "rb") as f:
                content = f.read()

            # Extract text from PDF
            text = self._extract_text_from_pdf(content)

            # Extract invoice date
            invoice_date = self._extract_invoice_date(text)

            # Extract cost amounts
            cost_euros, iva_euros = self._extract_amounts(text)

            # Create invoice object
            file_name = Path(file_path).name

            invoice = Invoice(
                invoice_date=invoice_date,
                concept="Electricity",  # Default value, will be overridden by caller
                type="Electricity",  # Default value, will be overridden by caller
                cost_euros=cost_euros,
                iva_euros=iva_euros,
                deductible_percentage=0,  # Will be set by the caller
                file_name=file_name,
                path=str(file_path),
            )

            self.logger.info(
                "Successfully extracted metadata from Repsol PDF file",
                file_path=file_path,
                file_name=file_name,
                invoice_date=invoice_date.isoformat(),
                cost_euros=float(cost_euros),
                iva_euros=float(iva_euros),
            )

            return invoice

        except Exception as e:
            self.logger.error(
                "Failed to extract metadata from Repsol PDF file",
                file_path=file_path,
                error=str(e),
            )
            raise ValueError(f"Failed to extract metadata from Repsol PDF file: {e}")

    def _extract_text_from_pdf(self, content: bytes) -> str:
        """Extract text content from Repsol PDF bytes."""
        try:
            # Try with pdfplumber first (better for complex layouts)
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                if text.strip():
                    return text

            # Fallback to PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

            return text

        except Exception as e:
            self.logger.error("Failed to extract text from Repsol PDF", error=str(e))
            raise ValueError(f"Failed to extract text from Repsol PDF: {e}")

    def _extract_invoice_date(self, text: str) -> datetime:
        """Extract invoice date from Repsol invoice text."""
        # Common date patterns in Spanish invoices
        date_patterns = [
            r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})",  # DD/MM/YYYY or DD-MM-YYYY
            r"(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})",  # YYYY/MM/DD or YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.group(1)) == 4:  # YYYY/MM/DD format
                    year, month, day = match.groups()
                else:  # DD/MM/YYYY format
                    day, month, year = match.groups()

                try:
                    return datetime(int(year), int(month), int(day))
                except ValueError:
                    continue

        # Try Spanish month names
        spanish_months = {
            "enero": 1,
            "febrero": 2,
            "marzo": 3,
            "abril": 4,
            "mayo": 5,
            "junio": 6,
            "julio": 7,
            "agosto": 8,
            "septiembre": 9,
            "octubre": 10,
            "noviembre": 11,
            "diciembre": 12,
        }

        for month_name, month_num in spanish_months.items():
            pattern = rf"(\d{{1,2}})\s+{month_name}\s+(\d{{4}})"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day, year = match.groups()
                try:
                    return datetime(int(year), month_num, int(day))
                except ValueError:
                    continue

        # If no date found, use current date as fallback
        self.logger.warning(
            "Could not extract invoice date from PDF, using current date"
        )
        return datetime.now()

    def _extract_amounts(self, text: str) -> tuple[Decimal, Decimal]:
        """Extract cost and IVA amounts from Repsol invoice text."""
        # Look for amounts with Euro symbol
        amount_patterns = [
            r"(\d+[.,]\d{2})\s*€",  # 123.45€
            r"€\s*(\d+[.,]\d{2})",  # €123.45
            r"(\d+[.,]\d{2})\s*EUR",  # 123.45 EUR
        ]

        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean and convert amount
                    amount_str = match.replace(",", ".")
                    amount = Decimal(amount_str)
                    if amount > 0:  # Only positive amounts
                        amounts.append(amount)
                except (ValueError, InvalidOperation):
                    continue

        if not amounts:
            self.logger.warning(
                "Could not extract amounts from PDF, using default values"
            )
            return Decimal("0.00"), Decimal("0.00")

        # Sort amounts in descending order
        amounts.sort(reverse=True)

        # Assume the largest amount is the total cost
        total_cost = amounts[0]

        # Look for IVA (VAT) amount specifically
        iva_patterns = [
            r"IVA[:\s]*(\d+[.,]\d{2})",  # IVA: 12.34
            r"(\d+[.,]\d{2})\s*IVA",  # 12.34 IVA
            r"21%[:\s]*(\d+[.,]\d{2})",  # 21%: 12.34
        ]

        iva_amount = Decimal("0.00")
        for pattern in iva_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    iva_str = match.group(1).replace(",", ".")
                    iva_amount = Decimal(iva_str)
                    break
                except (ValueError, InvalidOperation):
                    continue

        # If no specific IVA found, calculate it (assuming 21% Spanish VAT)
        if iva_amount == 0 and len(amounts) >= 2:
            # Second largest amount might be the base amount
            base_amount = amounts[1]
            iva_amount = total_cost - base_amount
        elif iva_amount == 0:
            # Calculate 21% of total as IVA
            iva_amount = total_cost * Decimal("0.21")

        return total_cost, iva_amount

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
            "[data-testid*='consent']",
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
                recent_pdfs = [
                    f for f in pdf_files if time.time() - f.stat().st_mtime < 10
                ]
                if recent_pdfs:
                    return recent_pdfs[0]

            time.sleep(0.5)

        raise TimeoutError(
            f"Download timeout: {filename} not found after {timeout} seconds"
        )
