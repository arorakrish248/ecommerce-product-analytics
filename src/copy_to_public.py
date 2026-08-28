import os
import shutil

public_dir = 'C:/Users/Public/ecommerce_analytics_data'
os.makedirs(public_dir, exist_ok=True)

src_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/processed'

files = [
    'dim_customers.csv',
    'dim_products.csv',
    'dim_sellers.csv',
    'fact_orders.csv',
    'fact_order_items.csv',
    'fact_order_payments.csv',
    'fact_order_reviews.csv'
]

for f in files:
    src_path = os.path.join(src_dir, f)
    dst_path = os.path.join(public_dir, f)
    shutil.copyfile(src_path, dst_path)
    print(f"Copied {f} to {public_dir} ({os.path.getsize(dst_path):,} bytes)")

print("\nAll files copied to C:/Users/Public/ecommerce_analytics_data/ with full public read access!")
