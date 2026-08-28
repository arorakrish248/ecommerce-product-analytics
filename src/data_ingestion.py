import os
import urllib.request

def run():
    print("Ingesting raw Olist datasets from official public repository...")
    raw_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/raw'
    os.makedirs(raw_dir, exist_ok=True)
    base_url = 'https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/'
    files = [
        'olist_customers_dataset.csv',
        'olist_order_items_dataset.csv',
        'olist_order_payments_dataset.csv',
        'olist_order_reviews_dataset.csv',
        'olist_orders_dataset.csv',
        'olist_products_dataset.csv',
        'olist_sellers_dataset.csv',
        'product_category_name_translation.csv'
    ]
    for f in files:
        dest = os.path.join(raw_dir, f)
        if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
            print(f"Downloading {f}...")
            urllib.request.urlretrieve(base_url + f, dest)
        print(f"Verified: {f} ({os.path.getsize(dest):,} bytes)")
    print("Data Ingestion Pipeline Complete!")

if __name__ == '__main__':
    run()
