#!/usr/bin/env python3
"""
Test for downloading a specific Repsol invoice (September 24th).
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

def test_repsol_download():
    """Test Repsol login and download September 24th invoice."""
    print("Starting Repsol download test...")
    
    # Get credentials from environment
    username = os.getenv('REPSOL_USERNAME')
    password = os.getenv('REPSOL_PASSWORD')
    
    if not username or not password:
        print("Error: REPSOL_USERNAME and REPSOL_PASSWORD environment variables must be set")
        return False
    
    driver = None
    try:
        # Setup Chrome options with download preferences
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        
        # Set download directory
        download_dir = artifacts_dir / "downloads"
        download_dir.mkdir(exist_ok=True)
        
        options.add_experimental_option(
            "prefs", {
                "download.default_directory": str(download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
        )
        
        # Start driver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to login page
        login_url = "https://areacliente.repsol.es/login"
        print(f"Navigating to {login_url}")
        driver.get(login_url)
        
        # Wait for the page to fully load (React app)
        print("Waiting for page to load...")
        time.sleep(10)
        
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
            time.sleep(15)  # Give more time for dynamic content
            
            # Take screenshot of invoices page
            invoices_screenshot = artifacts_dir / "repsol_invoices_download_test.png"
            driver.save_screenshot(str(invoices_screenshot))
            print(f"Invoices page screenshot saved: {invoices_screenshot}")
            
            # Look for download buttons
            print("Looking for download buttons...")
            
            # Try different selectors for download buttons
            download_selectors = [
                "[data-testid*='download']",
                "[data-cy*='download']",
                "button[title*='Descargar']",
                "a[title*='Descargar']",
                "button[aria-label*='Descargar']",
                "a[aria-label*='Descargar']"
            ]
            
            download_buttons = []
            for selector in download_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    download_buttons.extend(buttons)
                    print(f"Found {len(buttons)} buttons with selector: {selector}")
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
            
            # Also look for any button containing "Descargar" text
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(all_buttons)} total buttons on the page")
            
            for i, button in enumerate(all_buttons):
                try:
                    text = button.text.strip()
                    if "descargar" in text.lower():
                        download_buttons.append(button)
                        print(f"  Download button {len(download_buttons)}: '{text}'")
                    elif text:  # Show first few buttons for debugging
                        if i < 10:
                            print(f"  Button {i+1}: '{text}'")
                except:
                    continue
            
            print(f"Total download buttons found: {len(download_buttons)}")
            
            # Also check links
            all_links = driver.find_elements(By.TAG_NAME, "a")
            print(f"Found {len(all_links)} total links on the page")
            
            for i, link in enumerate(all_links):
                try:
                    text = link.text.strip()
                    if "descargar" in text.lower():
                        download_buttons.append(link)
                        print(f"  Download link {len(download_buttons)}: '{text}'")
                    elif text and i < 10:  # Show first few links for debugging
                        print(f"  Link {i+1}: '{text}'")
                except:
                    continue
            
            if download_buttons:
                # Try to click the first download button
                print("Attempting to click the first download button...")
                
                # Get initial files in download directory
                initial_files = set(f.name for f in download_dir.iterdir() if f.is_file())
                print(f"Initial files in download directory: {initial_files}")
                
                try:
                    # Scroll to the button to make sure it's visible
                    driver.execute_script("arguments[0].scrollIntoView(true);", download_buttons[0])
                    time.sleep(2)
                    
                    # Click the button
                    download_buttons[0].click()
                    print("Download button clicked!")
                    
                    # Wait for download to complete
                    print("Waiting for download to complete...")
                    time.sleep(10)
                    
                    # Check for new files
                    final_files = set(f.name for f in download_dir.iterdir() if f.is_file())
                    new_files = final_files - initial_files
                    
                    if new_files:
                        print(f"Download successful! New files: {new_files}")
                        
                        # Move the downloaded file to the main artifacts directory
                        for file_name in new_files:
                            downloaded_file = download_dir / file_name
                            if downloaded_file.exists():
                                # Rename to something more descriptive
                                new_name = f"repsol_invoice_september_24_{file_name}"
                                new_path = artifacts_dir / new_name
                                downloaded_file.rename(new_path)
                                print(f"Downloaded file saved as: {new_path}")
                        
                        return True
                    else:
                        print("No new files found after download attempt")
                        
                        # Check if there are any error messages on the page
                        error_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='error'], [class*='Error'], .alert, .warning")
                        if error_elements:
                            print("Error elements found on page:")
                            for elem in error_elements:
                                try:
                                    print(f"  - {elem.text}")
                                except:
                                    pass
                        
                        return False
                        
                except Exception as e:
                    print(f"Error clicking download button: {e}")
                    return False
            else:
                print("No download buttons found")
                
                # Save page source for debugging
                debug_source = artifacts_dir / "repsol_no_download_buttons.html"
                with open(debug_source, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"Page source saved for debugging: {debug_source}")
                
                return False
        else:
            print("Login failed - not redirected to inicio page")
            return False
        
    except Exception as e:
        print(f"Error during download test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_repsol_download()
    if success:
        print("Download test completed successfully")
    else:
        print("Download test failed")
        sys.exit(1)
