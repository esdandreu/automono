#!/usr/bin/env python3
"""
Improved test script for Repsol workflow.

This script handles cookie consent and other overlays that might block interactions.
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


def handle_cookie_consent(driver):
    """Handle cookie consent overlays."""
    try:
        # Common cookie consent selectors
        cookie_selectors = [
            "button[id*='accept']",
            "button[class*='accept']",
            "button[class*='cookie']",
            "button[class*='consent']",
            "button:contains('Aceptar')",
            "button:contains('Accept')",
            "button:contains('OK')",
            ".onetrust-close-btn-handler",
            "#onetrust-accept-btn-handler",
            "[data-cy*='accept']",
            "[data-testid*='accept']"
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_button = driver.find_element(By.CSS_SELECTOR, selector)
                if cookie_button.is_displayed():
                    logger.info(f"Found cookie consent button: {selector}")
                    cookie_button.click()
                    logger.info("Cookie consent accepted")
                    time.sleep(2)  # Wait for overlay to disappear
                    return True
            except:
                continue
        
        # Try to close any overlay by clicking outside or pressing escape
        try:
            from selenium.webdriver.common.keys import Keys
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass
            
        return False
    except Exception as e:
        logger.warning(f"Error handling cookie consent: {e}")
        return False


def test_repsol_workflow():
    """Test the complete Repsol workflow."""
    try:
        logger.info("Starting improved Repsol workflow test")
        
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
            handle_cookie_consent(driver)
            
            # Take a screenshot for debugging
            driver.save_screenshot("repsol_login_page_improved.png")
            logger.info("Screenshot saved as repsol_login_page_improved.png")
            
            # Look for login form elements
            logger.info("Looking for login form elements...")
            
            # Try different selectors for username field
            username_selectors = [
                "input[name='username']",
                "input[name='email']", 
                "input[name='user']",
                "input[type='email']",
                "input[type='text']",
                "#username",
                "#email",
                "#user"
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Found username field with selector: {selector}")
                    break
                except:
                    continue
            
            if not username_field:
                logger.error("Could not find username field")
                return False
            
            # Fill username
            username_field.clear()
            username_field.send_keys(username)
            logger.info("Username filled")
            
            # Look for password field
            password_selectors = [
                "input[name='password']",
                "input[name='pass']",
                "input[type='password']",
                "#password",
                "#pass"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Found password field with selector: {selector}")
                    break
                except:
                    continue
            
            if not password_field:
                logger.error("Could not find password field")
                return False
            
            # Fill password
            password_field.clear()
            password_field.send_keys(password)
            logger.info("Password filled")
            
            # Handle any additional overlays
            handle_cookie_consent(driver)
            
            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Entrar')",
                "button:contains('Login')",
                "button:contains('Iniciar')",
                ".login__submit",
                "[data-cy='login-submit-button']"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Found submit button with selector: {selector}")
                    break
                except:
                    continue
            
            if not submit_button:
                logger.error("Could not find submit button")
                return False
            
            # Try to click submit button with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Scroll to button if needed
                    driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                    time.sleep(1)
                    
                    # Try regular click
                    submit_button.click()
                    logger.info("Submit button clicked successfully")
                    break
                    
                except ElementClickInterceptedException:
                    logger.warning(f"Click intercepted on attempt {attempt + 1}")
                    
                    # Handle overlays again
                    handle_cookie_consent(driver)
                    
                    # Try JavaScript click
                    try:
                        driver.execute_script("arguments[0].click();", submit_button)
                        logger.info("Submit button clicked via JavaScript")
                        break
                    except Exception as e:
                        logger.warning(f"JavaScript click failed: {e}")
                        
                    if attempt == max_retries - 1:
                        raise Exception("Could not click submit button after all attempts")
            
            # Wait for navigation
            try:
                WebDriverWait(driver, 30).until(
                    lambda d: d.current_url != "https://areacliente.repsol.es/login"
                )
                logger.info("Login successful, redirected to:", driver.current_url)
            except TimeoutException:
                logger.warning("Login may have failed or taken longer than expected")
            
            # Take screenshot after login
            driver.save_screenshot("repsol_after_login_improved.png")
            logger.info("Screenshot after login saved")
            
            # Navigate to invoices page
            logger.info("Navigating to invoices page")
            driver.get("https://areacliente.repsol.es/mis-facturas")
            
            # Wait for invoices page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Invoices page loaded")
            
            # Handle any overlays on invoices page
            handle_cookie_consent(driver)
            
            # Take screenshot of invoices page
            driver.save_screenshot("repsol_invoices_page_improved.png")
            logger.info("Screenshot of invoices page saved")
            
            # Save page source for analysis
            with open("repsol_invoices_source_improved.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.info("Invoices page source saved")
            
            # Look for invoice elements
            logger.info("Looking for invoice elements...")
            
            # Common invoice selectors
            invoice_selectors = [
                ".factura",
                ".invoice",
                ".bill",
                "[data-invoice]",
                "tr[data-factura]",
                ".invoice-row",
                ".factura-row"
            ]
            
            invoices_found = []
            for selector in invoice_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        invoices_found.extend(elements)
                except:
                    continue
            
            if invoices_found:
                logger.info(f"Total invoice elements found: {len(invoices_found)}")
                
                # Try to find September 24th invoice
                target_date = datetime(2024, 9, 24)
                for i, invoice_element in enumerate(invoices_found[:5]):  # Check first 5
                    try:
                        text = invoice_element.text
                        logger.info(f"Invoice {i+1} text: {text[:100]}...")
                        
                        # Look for date patterns in the text
                        if "24" in text and "09" in text:
                            logger.info(f"Found potential September 24th invoice: {text[:200]}")
                            
                            # Look for download link
                            download_links = invoice_element.find_elements(By.CSS_SELECTOR, "a[href*='.pdf'], a[href*='download'], button[data-download]")
                            if download_links:
                                logger.info(f"Found {len(download_links)} download links")
                                # Try to click the first download link
                                try:
                                    download_links[0].click()
                                    logger.info("Download link clicked")
                                    time.sleep(3)  # Wait for download
                                except Exception as e:
                                    logger.warning(f"Could not click download link: {e}")
                    except Exception as e:
                        logger.warning(f"Error processing invoice element {i+1}: {e}")
            else:
                logger.warning("No invoice elements found")
            
            return True
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Repsol workflow test failed: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point."""
    print("🔍 Testing Improved Repsol Workflow")
    print("=" * 40)
    
    success = test_repsol_workflow()
    
    if success:
        print("✅ Repsol workflow test completed successfully!")
        print("📸 Screenshots and page sources saved for analysis")
    else:
        print("❌ Repsol workflow test failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


