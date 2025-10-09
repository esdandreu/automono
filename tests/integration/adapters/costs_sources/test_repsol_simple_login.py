#!/usr/bin/env python3
"""
Simple Repsol login test to debug the current page structure.
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

def test_repsol_login():
    """Test Repsol login and take screenshots for debugging."""
    print("Starting simple Repsol login test...")
    
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
        
        # Take screenshot of login page
        screenshot_file = artifacts_dir / "repsol_login_debug.png"
        driver.save_screenshot(str(screenshot_file))
        print(f"Screenshot saved: {screenshot_file}")
        
        # Save page source
        source_file = artifacts_dir / "repsol_login_debug.html"
        with open(source_file, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Page source saved: {source_file}")
        
        # Try to find username field with different selectors
        username_selectors = [
            "#mail",  # Found in the actual page
            "input[id='mail']",
            "input[name='email']",
            "input[id='email']",
            "input[type='email']",
            "input[placeholder*='email']",
            "input[placeholder*='usuario']",
            "input[placeholder*='correo']",
            "input[placeholder*='Email']",
            "input[placeholder*='Usuario']",
            "#email",
            ".email",
            "[data-testid='email']",
            "[data-cy='email']",
            "input[autocomplete='email']",
            "input[autocomplete='username']",
            "input[name='username']",
            "input[id='username']"
        ]
        
        # First, let's see what input elements are actually on the page
        print("Searching for all input elements on the page...")
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(all_inputs)} input elements:")
        for i, input_elem in enumerate(all_inputs):
            try:
                input_type = input_elem.get_attribute("type") or "text"
                input_name = input_elem.get_attribute("name") or "no-name"
                input_id = input_elem.get_attribute("id") or "no-id"
                input_placeholder = input_elem.get_attribute("placeholder") or "no-placeholder"
                print(f"  Input {i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
            except Exception as e:
                print(f"  Input {i+1}: Error getting attributes - {e}")
        
        username_field = None
        for selector in username_selectors:
            try:
                username_field = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"Found username field with selector: {selector}")
                break
            except NoSuchElementException:
                continue
        
        if username_field:
            print("Username field found successfully!")
            # Try to enter username
            username_field.clear()
            username_field.send_keys(username)
            print("Username entered successfully")
            
            # Look for password field
            password_selectors = [
                "#pass",  # Found in the actual page
                "input[id='pass']",
                "input[name='password']",
                "input[id='password']",
                "input[type='password']",
                "input[placeholder*='password']",
                "input[placeholder*='contraseña']",
                "#password",
                ".password",
                "[data-testid='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found password field with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if password_field:
                print("Password field found successfully!")
                password_field.clear()
                password_field.send_keys(password)
                print("Password entered successfully")
                
                # Look for login button
                login_selectors = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:contains('Iniciar')",
                    "button:contains('Login')",
                    "button:contains('Entrar')",
                    ".login-button",
                    ".btn-login",
                    "[data-testid='login']"
                ]
                
                login_button = None
                for selector in login_selectors:
                    try:
                        login_button = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"Found login button with selector: {selector}")
                        break
                    except NoSuchElementException:
                        continue
                
                if login_button:
                    print("Login button found successfully!")
                    # Take screenshot before clicking
                    before_screenshot = artifacts_dir / "repsol_before_login.png"
                    driver.save_screenshot(str(before_screenshot))
                    print(f"Screenshot before login saved: {before_screenshot}")
                    
                    # Click login button
                    login_button.click()
                    print("Login button clicked")
                    
                    # Wait for navigation
                    time.sleep(5)
                    
                    # Take screenshot after login attempt
                    after_screenshot = artifacts_dir / "repsol_after_login.png"
                    driver.save_screenshot(str(after_screenshot))
                    print(f"Screenshot after login saved: {after_screenshot}")
                    
                    # Save page source after login
                    after_source = artifacts_dir / "repsol_after_login.html"
                    with open(after_source, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"Page source after login saved: {after_source}")
                    
                    print(f"Current URL: {driver.current_url}")
                    return True
                else:
                    print("Login button not found")
            else:
                print("Password field not found")
        else:
            print("Username field not found")
        
        return False
        
    except Exception as e:
        print(f"Error during login test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_repsol_login()
    if success:
        print("Login test completed successfully")
    else:
        print("Login test failed")
        sys.exit(1)
