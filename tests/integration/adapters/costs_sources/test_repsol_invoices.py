#!/usr/bin/env python3
"""
Test for navigating to Repsol invoices page after login.
"""

import os
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Create artifacts directory - use absolute path to avoid confusion
artifacts_dir = Path("/Users/esdandreu/automono/tests/artifacts")
artifacts_dir.mkdir(parents=True, exist_ok=True)

def test_repsol_invoices():
    """Test Repsol login and navigate to invoices page."""
    print("Starting Repsol invoices test...")
    
    # Get credentials from environment
    username = os.getenv('REPSOL_USERNAME')
    password = os.getenv('REPSOL_PASSWORD')
    
    if not username or not password:
        print("Error: REPSOL_USERNAME and REPSOL_PASSWORD environment variables must be set")
        return False
    
    driver = None
    try:
        # Setup Chrome options
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        
        # Start driver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to login page
        login_url = "https://areacliente.repsol.es/login"
        print(f"Navigating to {login_url}")
        driver.get(login_url)
        
        # Wait for the page to fully load (React app)
        print("Waiting for page to load...")
        time.sleep(10)  # Give more time for React to render
        
        # Wait for any cookie consent banner and accept it
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            print("Accepted cookie consent")
            time.sleep(2)
        except TimeoutException:
            print("No cookie consent banner found")
        
        # Login
        print("Attempting to log in...")
        username_field = driver.find_element(By.ID, "mail")
        username_field.clear()
        username_field.send_keys(username)
        
        password_field = driver.find_element(By.ID, "pass")
        password_field.clear()
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for login to complete
        print("Waiting for login to complete...")
        time.sleep(5)
        
        # Check if we're logged in
        current_url = driver.current_url
        print(f"Current URL after login: {current_url}")
        
        if "inicio" in current_url:
            print("Login successful!")
            
            # Navigate to invoices page
            invoices_url = "https://areacliente.repsol.es/mis-facturas"
            print(f"Navigating to invoices page: {invoices_url}")
            driver.get(invoices_url)
            
            # Wait for the invoices page to load
            print("Waiting for invoices page to load...")
            time.sleep(10)
            
            # Take screenshot of invoices page
            invoices_screenshot = artifacts_dir / "repsol_invoices_page.png"
            driver.save_screenshot(str(invoices_screenshot))
            print(f"Invoices page screenshot saved: {invoices_screenshot}")
            
            # Save page source
            invoices_source = artifacts_dir / "repsol_invoices_page.html"
            with open(invoices_source, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"Invoices page source saved: {invoices_source}")
            
            # Look for invoice-related elements
            print("Searching for invoice elements...")
            
            # Look for common invoice-related text
            page_text = driver.page_source.lower()
            invoice_keywords = ["factura", "invoice", "descargar", "download", "pdf", "importe", "fecha"]
            found_keywords = [keyword for keyword in invoice_keywords if keyword in page_text]
            print(f"Found keywords in page: {found_keywords}")
            
            # Look for links that might be invoice downloads
            links = driver.find_elements(By.TAG_NAME, "a")
            print(f"Found {len(links)} links on the page")
            
            invoice_links = []
            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    text = link.text.strip()
                    if any(keyword in href.lower() or keyword in text.lower() for keyword in ["factura", "invoice", "descargar", "download", "pdf"]):
                        invoice_links.append({"href": href, "text": text})
                except:
                    continue
            
            print(f"Found {len(invoice_links)} potential invoice links:")
            for i, link in enumerate(invoice_links[:10]):  # Show first 10
                print(f"  Link {i+1}: {link['text'][:50]}... -> {link['href'][:100]}...")
            
            # Look for buttons that might trigger downloads
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(buttons)} buttons on the page")
            
            download_buttons = []
            for button in buttons:
                try:
                    text = button.text.strip()
                    onclick = button.get_attribute("onclick") or ""
                    if any(keyword in text.lower() or keyword in onclick.lower() for keyword in ["descargar", "download", "factura", "invoice"]):
                        download_buttons.append({"text": text, "onclick": onclick})
                except:
                    continue
            
            print(f"Found {len(download_buttons)} potential download buttons:")
            for i, button in enumerate(download_buttons[:10]):  # Show first 10
                print(f"  Button {i+1}: {button['text'][:50]}...")
            
            return True
        else:
            print("Login failed - not redirected to inicio page")
            return False
        
    except Exception as e:
        print(f"Error during invoices test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_repsol_invoices()
    if success:
        print("Invoices test completed successfully")
    else:
        print("Invoices test failed")
        sys.exit(1)
