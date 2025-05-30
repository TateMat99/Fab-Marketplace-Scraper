import os
import time
import json
import random
import csv
import re
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

JSON_FILE = os.path.join(DATA_DIR, "categories.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "all_products.csv")
HEADLESS_MODE = False  
PAGINATION_LIMIT= 4900


PRICE_RANGES = [(0, 1), (1, 5), (5, 10), (10, 20), (20, 50), (50, 100), (100, 10000)]
SORTING_METHODS = ["-relevance", "-createdAt", "createdAt", "-price", "price", "-averageRating"]


def random_delay():
    time.sleep(random.uniform(2, 5))

#Remove invalid characters from filenames
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name).replace('\n', ' ').strip()

#Initialize Selenium Chrome driver
def setup_driver():
    options = Options()
    if HEADLESS_MODE:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    return uc.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Load categories from the JSON file
def load_categories():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: Could not load categories.json")
        return {}
    
#Append list of product dicts to the output CSV file
def save_to_csv(products):
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "Title", "Price", "Seller", "Category", "Subcategory", "Rating", "Reviews",
            "Distribution Method", "Is Mature", "Available in Europe", "Tags",
            "Supported Unreal Engine Versions", "Supported Target Platforms",
            "Publish Date", "Last Updated", "Description"
        ])
        if file.tell() == 0:
            writer.writeheader()
        writer.writerows(products)
    print(f"Saved {len(products)} products to CSV.")
    return len(products)

#Fetch JSON data from Fab.com search API endpoint using Selenium driver
def fetch_api_data(driver, api_url, params):
    url_with_params = f"{api_url}?{params}"
    print(f"Fetching API: {url_with_params}")
    
    driver.get(url_with_params)
    random_delay()
    page_source = driver.page_source

    try:
        start = page_source.find('<pre>') + len('<pre>')
        end = page_source.find('</pre>', start)
        json_data = page_source[start:end].strip()
        return json.loads(json_data) if json_data else None
    except Exception:
        return None

#Scrape all products for a given category, using pagination, sorting, and price filtering.
def scrape_subcategory(driver, api_url, category_name, category_type, product_count):

    category_cleaned = category_type.split("/")[-1]
    listing_type_cleaned = category_type.split("/")[0]

    use_categories = category_cleaned and listing_type_cleaned != category_cleaned

    if product_count > PAGINATION_LIMIT:
        price_ranges = PRICE_RANGES
        sorting_methods = SORTING_METHODS
    else:
        price_ranges = [(None, None)]
        sorting_methods = ["-relevance"]

    for min_price, max_price in price_ranges:
        total_saved_products = 0
        
        for sorting in sorting_methods:
            print(f" Scraping {category_name} ({product_count} products) with Price Range {min_price}-{max_price}, Sorting: {sorting}")

            params = f"currency=USD&listing_types={listing_type_cleaned}&sort_by={sorting}"
            if use_categories:
                params = f"categories={category_cleaned}&{params}"
            if min_price is not None:
                params += f"&min_price={min_price}"
            if max_price is not None:
                params += f"&max_price={max_price}"

            products = []
            last_cursor = None  

            while True:
                product_data = fetch_api_data(driver, api_url, params)
                if not product_data:
                    print(f"No data fetched for {category_name}!")
                    break

                for product in product_data.get('results', []):
                    try:
                        product_entry = {
                            "Title": product.get("title", "N/A"),
                            "Price": f"${product.get('startingPrice', {}).get('price', 'N/A')}",
                            "Seller": product.get("user", {}).get("displayName", "Unknown"),
                            "Category": listing_type_cleaned.replace("-", " ").title(), 
                            "Subcategory": category_cleaned.replace("-", " ").title(), 
                            "Rating": product.get("averageRating", "No rating"),
                            "Reviews": product.get("reviewCount", "No reviews"),
                            "Distribution Method": product.get("assetFormats", [{}])[0].get("technicalSpecs", {}).get("unrealEngineDistributionMethod", "N/A"),
                            "Is Mature": product.get("isMature", "N/A"),
                            "Available in Europe": product.get("availableInEurope", "N/A"),
                            "Tags": ", ".join([tag.get("name", "N/A") for tag in product.get("tags", [])]),
                            "Supported Unreal Engine Versions": ", ".join(product.get("assetFormats", [{}])[0].get("technicalSpecs", {}).get("unrealEngineEngineVersions", [])),
                            "Supported Target Platforms": ", ".join(product.get("assetFormats", [{}])[0].get("technicalSpecs", {}).get("unrealEngineTargetPlatforms", [])),
                            "Publish Date": product.get("publishedAt", "N/A"),
                            "Last Updated": product.get("updatedAt", "N/A"),
                            "Description": product.get("assetFormats", [{}])[0].get("technicalSpecs", {}).get("technicalDetails", "No description")
                        }
                        products.append(product_entry)
                    except Exception as e:
                        print(f"Error processing product: {e}")

                next_cursor = product_data.get('cursors', {}).get('next', None)

                if not next_cursor:
                    print(f"Pagination limit reached for {category_name}.")
                    break

                if next_cursor == last_cursor:
                    print(f"Cursor has not changed ({next_cursor}) for {category_name}. Breaking loop to avoid infinite pagination.")
                    break  

                last_cursor = next_cursor
                params = params.split("&cursor=")[0] + f"&cursor={next_cursor}"

            total_saved_products += save_to_csv(products)

            if total_saved_products < product_count and total_saved_products < PAGINATION_LIMIT:
                print(f"Not enough products scraped ({total_saved_products}/{product_count}). Switching price range.")
                break

#Main function to scrape products from all categories loaded from JSON.
def scrape_products():
    print("Starting product scraping...")
    api_url = "https://www.fab.com/i/listings/search"
    categories = load_categories()

    if not categories:
        print("No categories found. Exiting.")
        return

    driver = setup_driver()
    
    for category_name, data in categories.items():
        category_type = data["type"]
        product_count = data.get("product_count", 0)
        print(f"Scraping products from: {category_name} ({product_count} products)")
        scrape_subcategory(driver, api_url, category_name, category_type, product_count)

    driver.quit()
    print("All products scraped successfully!")

if __name__ == "__main__":
    scrape_products()
