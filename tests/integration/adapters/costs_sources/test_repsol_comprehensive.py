#!/usr/bin/env python3
"""
Comprehensive test for Repsol invoice download with multiple approaches.
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

def test_repsol_comprehensive():
    """Comprehensive test for Repsol invoice download."""
    print("Starting comprehensive Repsol test...")
    
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
            invoices_screenshot = artifacts_dir / "repsol_comprehensive_test.png"
            driver.save_screenshot(str(invoices_screenshot))
            print(f"Invoices page screenshot saved: {invoices_screenshot}")
            
            # Save page source for analysis
            page_source = artifacts_dir / "repsol_comprehensive_source.html"
            with open(page_source, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"Page source saved: {page_source}")
            
            # Look for download buttons
            print("Looking for download buttons...")
            
            # Find all buttons with "Descargar" text
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            download_buttons = []
            
            for button in all_buttons:
                try:
                    text = button.text.strip()
                    if "descargar" in text.lower():
                        download_buttons.append(button)
                        print(f"Found download button: '{text}'")
                except:
                    continue
            
            print(f"Total download buttons found: {len(download_buttons)}")
            
            if download_buttons:
                # Try different approaches to trigger download
                for i, button in enumerate(download_buttons[:3]):  # Try first 3 buttons
                    print(f"\n--- Trying download button {i+1} ---")
                    
                    try:
                        # Get initial files
                        initial_files = set(f.name for f in download_dir.iterdir() if f.is_file())
                        
                        # Scroll to button
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(2)
                        
                        # Try different click methods
                        print("Trying regular click...")
                        button.click()
                        time.sleep(5)
                        
                        # Check for new files
                        final_files = set(f.name for f in download_dir.iterdir() if f.is_file())
                        new_files = final_files - initial_files
                        
                        if new_files:
                            print(f"Download successful with regular click! New files: {new_files}")
                            
                            # Move the downloaded file
                            for file_name in new_files:
                                downloaded_file = download_dir / file_name
                                if downloaded_file.exists():
                                    new_name = f"repsol_invoice_{i+1}_{file_name}"
                                    new_path = artifacts_dir / new_name
                                    downloaded_file.rename(new_path)
                                    print(f"Downloaded file saved as: {new_path}")
                            
                            return True
                        
                        # Try JavaScript click
                        print("Trying JavaScript click...")
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(5)
                        
                        # Check for new files again
                        final_files = set(f.name for f in download_dir.iterdir() if f.is_file())
                        new_files = final_files - initial_files
                        
                        if new_files:
                            print(f"Download successful with JavaScript click! New files: {new_files}")
                            
                            # Move the downloaded file
                            for file_name in new_files:
                                downloaded_file = download_dir / file_name
                                if downloaded_file.exists():
                                    new_name = f"repsol_invoice_js_{i+1}_{file_name}"
                                    new_path = artifacts_dir / new_name
                                    downloaded_file.rename(new_path)
                                    print(f"Downloaded file saved as: {new_path}")
                            
                            return True
                        
                        # Try double click
                        print("Trying double click...")
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(driver)
                        actions.double_click(button).perform()
                        time.sleep(5)
                        
                        # Check for new files again
                        final_files = set(f.name for f in download_dir.iterdir() if f.is_file())
                        new_files = final_files - initial_files
                        
                        if new_files:
                            print(f"Download successful with double click! New files: {new_files}")
                            
                            # Move the downloaded file
                            for file_name in new_files:
                                downloaded_file = download_dir / file_name
                                if downloaded_file.exists():
                                    new_name = f"repsol_invoice_double_{i+1}_{file_name}"
                                    new_path = artifacts_dir / new_name
                                    downloaded_file.rename(new_path)
                                    print(f"Downloaded file saved as: {new_path}")
                            
                            return True
                        
                        print(f"No download triggered with button {i+1}")
                        
                    except Exception as e:
                        print(f"Error with button {i+1}: {e}")
                        continue
                
                print("No download was successful with any button")
                return False
            else:
                print("No download buttons found")
                return False
        else:
            print("Login failed - not redirected to inicio page")
            return False
        
    except Exception as e:
        print(f"Error during comprehensive test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_repsol_comprehensive()
    if success:
        print("Comprehensive test completed successfully")
    else:
        print("Comprehensive test failed")
        sys.exit(1)
