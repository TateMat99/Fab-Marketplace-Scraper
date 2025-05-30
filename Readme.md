# 🛍️ Fab.com Marketplace Data Scraper & Cleaner

This project scrapes product data from the Fab.com marketplace, cleans and normalizes it, preparing CSV datasets for analysis and visualization.

---

## 🚀 Features

- Scrapes all product categories and subcategories from Fab.com.
- Collects detailed product information including pricing, ratings, tags, and technical specifications.
- Cleans raw data by removing HTML, fixing dates, formatting prices, and handling missing values.
- Normalizes multi-value columns (tags, supported engine versions, target platforms) into separate relational CSV tables.
- Outputs clean CSV files for Power BI, Tableau, or other tools.

---

## 🗂️ Project Structure

- `scripts/` — Contains all Python scripts:
  - `01_Scrape_Categories.py` — Scrapes main and subcategories, saving to `data/categories.json`.
  - `02_Scrape_Products.py` — Scrapes product listings by category, saving raw data to `data/all_products.csv`.
  - `03_Clean_Data.py` — Cleans and normalizes raw product data, generating:

- `data/` — Contains all data files:
  - `categories.json`
  - `all_products.csv`
  - `products.csv`
  - `product_tags.csv`
  - `product_versions.csv`
  - `product_platforms.csv`

---

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/TateMat99/Fab-Marketplace-Scraper.git
cd fab-marketplace-scraper
```


### 2. Create and Activate a Virtual Environment (Recommended)

Create a Python virtual environment to isolate dependencies:

macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows

```bash
python -m venv venv
venv\Scripts\activate
```


### 3. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

---



## ⚙️ Usage

### 1: Scrape categories from Fab.com

```bash
python 01_Scrape_Categories.py
```
Fetches main categories and subcategories from Fab.com and saves them as JSON (data/categories.json).


### 2: Scrape product data using category info

```bash
python 02_ScrapeProductss.py
```
Uses the saved categories to scrape product details from Fab.com APIs and saves raw data as CSV


### 3: Clean and normalize scraped product data

```
Bash
python 03_Clean_Data.py
```
processes the raw scraped CSV data, cleans and formats fields, generates unique IDs, and normalizes multi-value fields (tags, supported engine versions, platforms).
