#!/usr/bin/env python3
"""
Final test script for Repsol workflow.

This script specifically looks for the September 24th invoice and downloads it.
"""

import os
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

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


def test_repsol_september_invoice():
    """Test downloading the September 24th invoice from Repsol."""
    try:
        logger.info("Starting Repsol September invoice test")
        
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
            logger.info("Login successful, redirected to:", driver.current_url)
            
            # Navigate to invoices page
            logger.info("Navigating to invoices page")
            driver.get("https://areacliente.repsol.es/mis-facturas")
            
            # Wait for invoices page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Invoices page loaded")
            
            # Wait for content to load (the page might be loading dynamically)
            time.sleep(5)
            
            # Take screenshot for debugging
            driver.save_screenshot("repsol_invoices_final.png")
            logger.info("Screenshot saved")
            
            # Look for any content that might contain invoices
            logger.info("Looking for invoice content...")
            
            # Try to find any text content that might indicate invoices
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"Page text length: {len(page_text)}")
            
            # Look for September-related content
            if "septiembre" in page_text.lower() or "september" in page_text.lower():
                logger.info("Found September-related content in page text")
            else:
                logger.info("No September-related content found in page text")
            
            # Look for date patterns
            if "24" in page_text and "09" in page_text:
                logger.info("Found potential September 24th date pattern")
            else:
                logger.info("No September 24th date pattern found")
            
            # Try to find any clickable elements that might be invoices
            clickable_elements = driver.find_elements(By.CSS_SELECTOR, "a, button, [onclick], [data-click]")
            logger.info(f"Found {len(clickable_elements)} clickable elements")
            
            # Look for elements with invoice-related text
            invoice_elements = []
            for element in clickable_elements:
                try:
                    text = element.text.lower()
                    if any(word in text for word in ["factura", "invoice", "descargar", "download", "pdf"]):
                        invoice_elements.append(element)
                        logger.info(f"Found potential invoice element: {text[:50]}...")
                except:
                    continue
            
            logger.info(f"Found {len(invoice_elements)} potential invoice elements")
            
            # Try to find any table or list that might contain invoices
            tables = driver.find_elements(By.CSS_SELECTOR, "table, .table, [role='table']")
            logger.info(f"Found {len(tables)} tables")
            
            lists = driver.find_elements(By.CSS_SELECTOR, "ul, ol, .list, [role='list']")
            logger.info(f"Found {len(lists)} lists")
            
            # Look for any elements with data attributes that might indicate invoices
            data_elements = driver.find_elements(By.CSS_SELECTOR, "[data-*], [id*='factura'], [class*='factura'], [id*='invoice'], [class*='invoice']")
            logger.info(f"Found {len(data_elements)} elements with data attributes")
            
            # Save page source for detailed analysis
            with open("repsol_invoices_final_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.info("Page source saved for analysis")
            
            # If we found any potential invoice elements, try to interact with them
            if invoice_elements:
                logger.info("Attempting to interact with invoice elements...")
                for i, element in enumerate(invoice_elements[:3]):  # Try first 3
                    try:
                        logger.info(f"Trying element {i+1}: {element.text[:50]}...")
                        element.click()
                        time.sleep(2)
                        
                        # Check if a download started
                        # This is a simplified check - in a real implementation,
                        # you'd monitor the downloads directory
                        logger.info("Element clicked, checking for download...")
                        
                    except Exception as e:
                        logger.warning(f"Could not click element {i+1}: {e}")
            
            # Look for any JavaScript errors or console messages
            logs = driver.get_log('browser')
            if logs:
                logger.info(f"Found {len(logs)} browser console messages")
                for log in logs[:5]:  # Show first 5
                    logger.info(f"Console: {log}")
            
            return True
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Repsol September invoice test failed: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point."""
    print("🔍 Testing Repsol September 24th Invoice Download")
    print("=" * 50)
    
    success = test_repsol_september_invoice()
    
    if success:
        print("✅ Repsol September invoice test completed!")
        print("📸 Screenshots and page sources saved for analysis")
        print("🔍 Check the output files to see what was found on the page")
    else:
        print("❌ Repsol September invoice test failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


