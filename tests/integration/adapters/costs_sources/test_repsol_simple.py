#!/usr/bin/env python3
"""
Simple test script for Repsol workflow.

This script tests the Repsol costs source adapter without the full settings system.
"""

import os
import sys
from pathlib import Path

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
from webdriver_manager.chrome import ChromeDriverManager


def test_repsol_website():
    """Test accessing the Repsol website directly."""
    try:
        logger.info("Starting Repsol website test")
        
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
        
        # Initialize driver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            # Navigate to Repsol login page
            logger.info("Navigating to Repsol login page")
            driver.get("https://areacliente.repsol.es/login")
            
            # Wait for page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Page loaded successfully")
            
            # Take a screenshot for debugging
            driver.save_screenshot("repsol_login_page.png")
            logger.info("Screenshot saved as repsol_login_page.png")
            
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
                # Print page source for debugging
                with open("repsol_page_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logger.info("Page source saved as repsol_page_source.html")
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
            
            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Entrar')",
                "button:contains('Login')",
                "button:contains('Iniciar')",
                ".login-btn",
                ".submit-btn"
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
            
            # Click submit
            submit_button.click()
            logger.info("Submit button clicked")
            
            # Wait for navigation
            WebDriverWait(driver, 30).until(
                lambda d: d.current_url != "https://areacliente.repsol.es/login"
            )
            
            logger.info("Login successful, redirected to:", driver.current_url)
            
            # Take screenshot after login
            driver.save_screenshot("repsol_after_login.png")
            logger.info("Screenshot after login saved as repsol_after_login.png")
            
            # Navigate to invoices page
            logger.info("Navigating to invoices page")
            driver.get("https://areacliente.repsol.es/mis-facturas")
            
            # Wait for invoices page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Invoices page loaded")
            
            # Take screenshot of invoices page
            driver.save_screenshot("repsol_invoices_page.png")
            logger.info("Screenshot of invoices page saved as repsol_invoices_page.png")
            
            # Save page source for analysis
            with open("repsol_invoices_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.info("Invoices page source saved as repsol_invoices_source.html")
            
            return True
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Repsol website test failed: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point."""
    print("🔍 Testing Repsol Website Access")
    print("=" * 40)
    
    success = test_repsol_website()
    
    if success:
        print("✅ Repsol website test completed successfully!")
        print("📸 Screenshots and page sources saved for analysis")
    else:
        print("❌ Repsol website test failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
