import os
import time
import json
import re
import random
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    StaleElementReferenceException, TimeoutException, NoSuchElementException
)

# Set up base and data directories for saving output files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
JSON_FILE = os.path.join(DATA_DIR, "categories.json")


HEADLESS_MODE = False  
visited_subcategories = set()


def random_delay(short=False):
    time.sleep(random.uniform(2, 5) if short else random.uniform(7, 15))

# clean caregorie texts
def clean_text(text):
    return re.sub(r'\d+(\.\d+)?[KMB]?', '', text).strip()

# convert product count strings to int
def parse_product_count(text):
    text = text.replace(',', '').strip()

    if 'K' in text:
        return int(float(text.replace('K', '')) * 1000)
    elif 'M' in text:
        return int(float(text.replace('M', '')) * 1000000)
    
    try:
        return int(text)
    except ValueError:
        return 0  

# initialize Selenium Webdriver
def setup_driver():
    options = Options()
    if HEADLESS_MODE:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    return uc.Chrome(service=Service(ChromeDriverManager().install()), options=options)

#Load existing categories from the JSON file, if it exists.
def load_existing_categories():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save category data to JSON file.
def save_category_to_json(category_name, category_type, category_url, product_count):
    categories = load_existing_categories()
    categories[f"{category_name} - {category_type}"] = {
        "type": category_type,
        "url": category_url,
        "product_count": product_count  
    }
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=4)

    print(f"Saved: {category_name} (Type: {category_type}, Products: {product_count})")

#Fetch main categories from the Fab.com categories page.
def fetch_categories(driver, website_url):
    print("Fetching main categories...")

    driver.get(website_url)
    random_delay()

    visited_categories = set()

    while True: 
        found_new_category = False  

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/category/"]'))
            )
            main_category_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/category/"]')

            for main_category in main_category_elements:
                try:
                    category_name = clean_text(main_category.text)
                    category_link = main_category.get_attribute("href")

                    if not category_link or "Trending" in category_name:
                        continue  

                    category_type = category_link.split("/category/")[-1]
                    key = f"{category_name} - {category_type}"

                    existing_categories = load_existing_categories()
                    if key in existing_categories or key in visited_categories:
                        print(f"Skipping already scraped category: {category_name} (Type: {category_type})")
                        continue  

                    visited_categories.add(key)  
                    found_new_category = True

                    try:
                        product_count_elem = main_category.find_element(By.CSS_SELECTOR, "span.fabkit-Counter-root")
                        product_count = parse_product_count(product_count_elem.text)
                    except NoSuchElementException:
                        product_count = 0  

                    print(f"Scraping main category: {category_name} (Products: {product_count})")
                    save_category_to_json(category_name, category_type, category_link, product_count)

                    driver.get(category_link)
                    random_delay(short=True)

                    fetch_subcategories(driver, category_link)

                    print(f"Returning to main categories page...")
                    driver.get(website_url)  
                    random_delay()

                    break  

                except StaleElementReferenceException:
                    print("Stale element detected. Re-fetching categories...")
                    break  

            if not found_new_category:  
                print("All main categories processed. Exiting loop.")
                return  

        except TimeoutException:
            print("Error: Page failed to load. Exiting.")
            return  


#Recursively fetch subcategories from a given category URL.
def fetch_subcategories(driver, category_url):
    subcategory_queue = [category_url]  

    while subcategory_queue:
        current_category = subcategory_queue.pop(0)  

        if current_category in visited_subcategories:
            continue  

        print(f"Fetching subcategories → {current_category}")
        visited_subcategories.add(current_category)

        driver.get(current_category)
        random_delay(short=True)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/category/"]'))
            )
        except TimeoutException:
            print(f"Warning: Subcategory page load timeout. Skipping {current_category}.")
            continue  

        subcategory_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/category/"]')

        for subcategory in subcategory_elements:
            subcategory_name = clean_text(subcategory.text)
            subcategory_link = subcategory.get_attribute("href")

            if subcategory_name and subcategory_link:
                if "all products" in subcategory_name.lower():  
                    continue  
                if subcategory_link in visited_subcategories:
                    continue  

                has_children = "fabkit-TreeView--noChildren" not in subcategory.get_attribute("class")

                try:
                    product_count_elem = subcategory.find_element(By.CSS_SELECTOR, "span.fabkit-Counter-root")
                    product_count = parse_product_count(product_count_elem.text)
                except NoSuchElementException:
                    product_count = 0  

                print(f"Scraping subcategory: {subcategory_name} (Has Children: {has_children}, Products: {product_count})")

                save_category_to_json(
                    subcategory_name,
                    subcategory_link.split("/category/")[-1],
                    subcategory_link,
                    product_count
                )

                if has_children:  
                    subcategory_queue.append(subcategory_link)  

        print(f"Finished subcategories. Returning to parent category.")


def scrape_categories():
    website_url = "https://www.fab.com/category"
    driver = setup_driver()
    fetch_categories(driver, website_url)
    driver.quit()

if __name__ == "__main__":
    scrape_categories()
