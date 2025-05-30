import os
import pandas as pd
import html
from bs4 import BeautifulSoup
from datetime import datetime
import re
import uuid

#Setup paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_csv = os.path.join(base_dir, "data", "all_products.csv")
output_main = os.path.join(base_dir, "data", "products.csv")
output_tags = os.path.join(base_dir, "data", "product_tags.csv")
output_versions = os.path.join(base_dir, "data", "product_versions.csv")
output_platforms = os.path.join(base_dir, "data", "product_platforms.csv")

#Load data
df = pd.read_csv(input_csv, quotechar='"', dtype=str, keep_default_na=False)

#Clean general formatting
df = df.map(lambda x: str(x).replace("|", " ") if isinstance(x, str) else x)

def clean_newlines(value):
    if isinstance(value, str):
        return re.sub(r'[\r\n]+', ' ', value).strip()
    return value

df = df.map(clean_newlines)

def clean_html(text):
    text = html.unescape(str(text))
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

df['Description'] = df['Description'].map(clean_html)

def clean_price(price):
    price = str(price).replace("$", "").replace(",", "")
    return float(price) if price.replace('.', '', 1).isdigit() else "N/A"

df['Price'] = df['Price'].map(clean_price)

def clean_numeric_column(column):
    return pd.to_numeric(column, errors='coerce').fillna("N/A")

df['Rating'] = clean_numeric_column(df['Rating'])
df['Reviews'] = clean_numeric_column(df['Reviews'])

def clean_text_column(column):
    return column.astype(str).str.strip().replace("", "N/A")

for col in ['Title', 'Seller', 'Category', 'Subcategory']:
    df[col] = clean_text_column(df[col])

def clean_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "N/A"

df['Publish Date'] = df['Publish Date'].map(clean_date)
df['Last Updated'] = df['Last Updated'].map(clean_date)

def fix_publish_date(row):
    if row['Publish Date'] == "N/A":
        return row['Last Updated'] if row['Last Updated'] != "N/A" else "2000-01-01 00:00:00"
    return row['Publish Date']

df['Publish Date'] = df.apply(fix_publish_date, axis=1)
df['Last Updated'] = df.apply(lambda row: row['Publish Date'] if row['Last Updated'] == "N/A" else row['Last Updated'], axis=1)

#Add ProductID
df.insert(0, 'ProductID', [str(uuid.uuid4()) for _ in range(len(df))])

#Save main product table
main_df = df.drop(columns=['Tags', 'Supported Unreal Engine Versions', 'Supported Target Platforms'])
main_df.to_csv(output_main, index=False, sep=",", quotechar='"', encoding="utf-8")

#Normalize multi-value fields

def explode_column(df, colname, output_file):
    rows = []
    for _, row in df.iterrows():
        product_id = row['ProductID']
        values = [v.strip() for v in str(row[colname]).split(',') if v.strip()]
        for val in values:
            rows.append({'ProductID': product_id, colname: val})
    pd.DataFrame(rows).drop_duplicates().to_csv(output_file, index=False, sep=",", quotechar='"', encoding="utf-8")

#Write normalized tables
explode_column(df, 'Tags', output_tags)
explode_column(df, 'Supported Unreal Engine Versions', output_versions)
explode_column(df, 'Supported Target Platforms', output_platforms)

print("Files Saved")
print(f"🟢 {output_main}")
print(f"🟢 {output_tags}")
print(f"🟢 {output_versions}")
print(f"🟢 {output_platforms}")
