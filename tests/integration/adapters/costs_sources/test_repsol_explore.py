#!/usr/bin/env python3
"""
Comprehensive exploration of the Repsol invoice page to understand its structure.
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

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Create artifacts directory
artifacts_dir = project_root / 'tests' / 'artifacts'
artifacts_dir.mkdir(parents=True, exist_ok=True)

def explore_page_structure(driver):
    """Explore the page structure to understand what elements are present."""
    print("=== PAGE STRUCTURE EXPLORATION ===")
    
    # Get page title and URL
    print(f"Page Title: {driver.title}")
    print(f"Current URL: {driver.current_url}")
    print()
    
    # Look for main content areas
    print("=== MAIN CONTENT AREAS ===")
    main_selectors = [
        "main", "content", "container", "wrapper", 
        "[role='main']", ".main-content", "#main", "#content"
    ]
    
    for selector in main_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"Found {len(elements)} element(s) with selector: {selector}")
                for i, elem in enumerate(elements[:3]):  # Show first 3
                    print(f"  Element {i+1}: {elem.tag_name} - {elem.get_attribute('class') or 'no class'}")
        except Exception as e:
            print(f"Error with selector {selector}: {e}")
    
    print()
    
    # Look for any tables
    print("=== TABLES ===")
    tables = driver.find_elements(By.TAG_NAME, "table")
    print(f"Found {len(tables)} table(s)")
    for i, table in enumerate(tables):
        print(f"  Table {i+1}:")
        print(f"    Classes: {table.get_attribute('class') or 'no class'}")
        print(f"    ID: {table.get_attribute('id') or 'no id'}")
        rows = table.find_elements(By.TAG_NAME, "tr")
        print(f"    Rows: {len(rows)}")
        if rows:
            cells = rows[0].find_elements(By.TAG_NAME, "td")
            print(f"    First row cells: {len(cells)}")
    
    print()
    
    # Look for lists
    print("=== LISTS ===")
    lists = driver.find_elements(By.TAG_NAME, "ul")
    print(f"Found {len(lists)} ul list(s)")
    for i, ul in enumerate(lists):
        print(f"  List {i+1}:")
        print(f"    Classes: {ul.get_attribute('class') or 'no class'}")
        print(f"    ID: {ul.get_attribute('id') or 'no id'}")
        items = ul.find_elements(By.TAG_NAME, "li")
        print(f"    Items: {len(items)}")
        if items:
            print(f"    First item text: {items[0].text[:100]}...")
    
    print()
    
    # Look for divs with invoice-related classes
    print("=== INVOICE-RELATED DIVS ===")
    invoice_keywords = ["invoice", "factura", "bill", "document", "file", "download"]
    for keyword in invoice_keywords:
        selectors = [
            f"div[class*='{keyword}']",
            f"div[id*='{keyword}']",
            f"[class*='{keyword}']",
            f"[id*='{keyword}']"
        ]
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} element(s) with keyword '{keyword}': {selector}")
                    for elem in elements[:2]:  # Show first 2
                        print(f"  {elem.tag_name} - {elem.get_attribute('class') or 'no class'} - {elem.text[:50]}...")
            except Exception as e:
                pass
    
    print()
    
    # Look for buttons and links
    print("=== BUTTONS AND LINKS ===")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    links = driver.find_elements(By.TAG_NAME, "a")
    
    print(f"Found {len(buttons)} button(s)")
    for i, btn in enumerate(buttons[:5]):  # Show first 5
        text = btn.text.strip()
        if text:
            print(f"  Button {i+1}: '{text}' - {btn.get_attribute('class') or 'no class'}")
    
    print(f"Found {len(links)} link(s)")
    for i, link in enumerate(links[:5]):  # Show first 5
        text = link.text.strip()
        href = link.get_attribute('href')
        if text or href:
            print(f"  Link {i+1}: '{text}' -> {href}")
    
    print()
    
    # Look for any elements with text containing dates
    print("=== ELEMENTS WITH DATES ===")
    date_patterns = ["2024", "septiembre", "september", "24", "09", "2023"]
    for pattern in date_patterns:
        try:
            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{pattern}')]")
            if elements:
                print(f"Found {len(elements)} element(s) containing '{pattern}':")
                for elem in elements[:3]:  # Show first 3
                    print(f"  {elem.tag_name}: {elem.text[:100]}...")
        except Exception as e:
            pass
    
    print()
    
    # Look for any loading indicators or dynamic content
    print("=== LOADING/DYNAMIC CONTENT ===")
    loading_selectors = [
        "[class*='loading']", "[class*='spinner']", "[class*='loader']",
        "[id*='loading']", "[id*='spinner']", "[id*='loader']"
    ]
    
    for selector in loading_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"Found {len(elements)} loading element(s): {selector}")
        except Exception as e:
            pass

def main():
    # Load credentials from environment
    username = os.getenv('REPSOL_USERNAME')
    password = os.getenv('REPSOL_PASSWORD')
    
    if not username or not password:
        print("Error: REPSOL_USERNAME and REPSOL_PASSWORD environment variables must be set")
        return
    
    # Setup Chrome options
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    
    # Initialize driver
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print("Starting Repsol page exploration...")
        
        # Navigate to login page
        driver.get("https://areacliente.repsol.es/login")
        print("Navigated to login page")
        
        # Accept cookies if present
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
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        username_field.send_keys(username)
        
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        print("Submitted login form")
        
        # Wait for login to complete
        WebDriverWait(driver, 20).until(
            lambda d: "/inicio" in d.current_url or "mis-facturas" in d.current_url
        )
        print("Login successful")
        
        # Navigate to invoices page
        driver.get("https://areacliente.repsol.es/mis-facturas")
        print("Navigated to invoices page")
        
        # Wait for page to load
        time.sleep(5)
        
        # Explore the page structure
        explore_page_structure(driver)
        
        # Wait a bit more for any dynamic content to load
        print("\nWaiting for dynamic content to load...")
        time.sleep(10)
        
        # Explore again after waiting
        print("\n=== SECOND EXPLORATION (after waiting) ===")
        explore_page_structure(driver)
        
        # Save page source for analysis
        source_file = artifacts_dir / "repsol_exploration_source.html"
        with open(source_file, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"\nSaved page source to {source_file}")
        
    except Exception as e:
        print(f"Error during exploration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("Exploration completed")

if __name__ == "__main__":
    main()


