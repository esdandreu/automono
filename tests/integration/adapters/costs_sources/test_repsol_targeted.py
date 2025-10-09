#!/usr/bin/env python3
"""
Targeted test script for Repsol workflow.

This script focuses on the specific "facturas" element we found and explores the page structure.
"""

import os
import sys
from pathlib import Path
import time

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Create artifacts directory
artifacts_dir = project_root / 'tests' / 'artifacts'
artifacts_dir.mkdir(parents=True, exist_ok=True)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple logging setup
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import selenium components directly
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager


def test_repsol_targeted():
    """Test the specific facturas element we found."""
    try:
        logger.info("Starting targeted Repsol test")
        
        # Get credentials
        username = os.getenv("REPSOL_USERNAME")
        password = os.getenv("REPSOL_PASSWORD")
        
        if not username or not password:
            logger.error("REPSOL_USERNAME and REPSOL_PASSWORD must be set in environment")
            return False
        
        logger.info(f"Credentials loaded for user: {username}")
        
        # Setup Chrome options
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Hide automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            # Navigate to Repsol login page
            logger.info("Navigating to Repsol login page")
            driver.get("https://areacliente.repsol.es/login")
            
            # Wait for page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Page loaded successfully")
            
            # Handle cookie consent
            try:
                cookie_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
                if cookie_button.is_displayed():
                    cookie_button.click()
                    logger.info("Cookie consent accepted")
                    time.sleep(2)
            except:
                logger.info("No cookie consent found or already accepted")
            
            # Fill login form
            username_field = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            username_field.clear()
            username_field.send_keys(username)
            logger.info("Username filled")
            
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(password)
            logger.info("Password filled")
            
            # Click submit
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            logger.info("Submit button clicked")
            
            # Wait for navigation
            WebDriverWait(driver, 30).until(
                lambda d: d.current_url != "https://areacliente.repsol.es/login"
            )
            logger.info(f"Login successful, redirected to: {driver.current_url}")
            
            # Navigate to invoices page
            logger.info("Navigating to invoices page")
            driver.get("https://areacliente.repsol.es/mis-facturas")
            
            # Wait for invoices page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Invoices page loaded")
            
            # Wait for content to load
            time.sleep(5)
            
            # Take initial screenshot
            driver.save_screenshot("repsol_initial.png")
            logger.info("Initial screenshot saved")
            
            # Look for the "facturas" element we found earlier
            logger.info("Looking for facturas element...")
            
            # Try different selectors for the facturas element
            facturas_selectors = [
                "a:contains('facturas')",
                "button:contains('facturas')",
                "[href*='facturas']",
                "[onclick*='facturas']",
                "a[href*='factura']",
                "button[onclick*='factura']"
            ]
            
            facturas_element = None
            for selector in facturas_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        facturas_element = elements[0]
                        logger.info(f"Found facturas element with selector: {selector}")
                        break
                except:
                    continue
            
            if not facturas_element:
                # Try to find any element containing "facturas" text
                all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'facturas') or contains(text(), 'Facturas')]")
                if all_elements:
                    facturas_element = all_elements[0]
                    logger.info("Found facturas element using XPath text search")
            
            if facturas_element:
                logger.info(f"Facturas element found: {facturas_element.tag_name} - {facturas_element.text}")
                
                # Try to click the facturas element
                try:
                    logger.info("Attempting to click facturas element...")
                    facturas_element.click()
                    time.sleep(3)
                    
                    # Take screenshot after clicking
                    driver.save_screenshot("repsol_after_facturas_click.png")
                    logger.info("Screenshot after facturas click saved")
                    
                    # Check if URL changed
                    current_url = driver.current_url
                    logger.info(f"Current URL after click: {current_url}")
                    
                    # Look for invoice content on the new page
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    logger.info(f"Page text length after click: {len(page_text)}")
                    
                    # Look for September-related content
                    if "septiembre" in page_text.lower() or "september" in page_text.lower():
                        logger.info("Found September-related content!")
                    
                    # Look for date patterns
                    if "24" in page_text and "09" in page_text:
                        logger.info("Found potential September 24th date pattern!")
                    
                    # Look for any download links or buttons
                    download_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='.pdf'], a[href*='download'], button[onclick*='download'], [data-download]")
                    logger.info(f"Found {len(download_elements)} potential download elements")
                    
                    for i, element in enumerate(download_elements[:5]):
                        try:
                            text = element.text
                            href = element.get_attribute("href") or ""
                            onclick = element.get_attribute("onclick") or ""
                            logger.info(f"Download element {i+1}: {text[:50]}... href: {href[:50]}... onclick: {onclick[:50]}...")
                        except:
                            continue
                    
                except Exception as e:
                    logger.warning(f"Could not click facturas element: {e}")
            else:
                logger.warning("No facturas element found")
            
            # Save final page source
            source_file = artifacts_dir / "repsol_final_source.html"
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.info(f"Final page source saved to {source_file}")
            
            return True
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Targeted Repsol test failed: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point."""
    print("🔍 Testing Repsol Targeted Facturas Element")
    print("=" * 45)
    
    success = test_repsol_targeted()
    
    if success:
        print("✅ Targeted Repsol test completed!")
        print("📸 Screenshots and page sources saved for analysis")
    else:
        print("❌ Targeted Repsol test failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


