import os
import pandas as pd
import numpy as np

def run():
    print("Running Data Cleaning & Transformation Pipeline...")
    raw_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/raw'
    proc_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/processed'
    os.makedirs(proc_dir, exist_ok=True)

    customers = pd.read_csv(os.path.join(raw_dir, 'olist_customers_dataset.csv'))
    orders = pd.read_csv(os.path.join(raw_dir, 'olist_orders_dataset.csv'))
    order_items = pd.read_csv(os.path.join(raw_dir, 'olist_order_items_dataset.csv'))
    payments = pd.read_csv(os.path.join(raw_dir, 'olist_order_payments_dataset.csv'))
    reviews = pd.read_csv(os.path.join(raw_dir, 'olist_order_reviews_dataset.csv'))
    products = pd.read_csv(os.path.join(raw_dir, 'olist_products_dataset.csv'))
    sellers = pd.read_csv(os.path.join(raw_dir, 'olist_sellers_dataset.csv'))
    translations = pd.read_csv(os.path.join(raw_dir, 'product_category_name_translation.csv'))

    # Datetime conversions
    date_cols = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date', 'order_estimated_delivery_date']
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col], errors='coerce')

    order_items['shipping_limit_date'] = pd.to_datetime(order_items['shipping_limit_date'], errors='coerce')
    reviews['review_creation_date'] = pd.to_datetime(reviews['review_creation_date'], errors='coerce')
    reviews['review_answer_timestamp'] = pd.to_datetime(reviews['review_answer_timestamp'], errors='coerce')

    # Join English category translations
    products = products.merge(translations, on='product_category_name', how='left')
    products['product_category_name_english'] = products['product_category_name_english'].fillna(products['product_category_name']).fillna('other')

    # Feature Engineering
    orders['delivery_days'] = (orders['order_delivered_customer_date'] - orders['order_purchase_timestamp']).dt.total_seconds() / 86400.0
    orders['estimated_days'] = (orders['order_estimated_delivery_date'] - orders['order_purchase_timestamp']).dt.total_seconds() / 86400.0
    orders['carrier_handling_days'] = (orders['order_delivered_carrier_date'] - orders['order_approved_at']).dt.total_seconds() / 86400.0
    orders['transit_days'] = (orders['order_delivered_customer_date'] - orders['order_delivered_carrier_date']).dt.total_seconds() / 86400.0
    orders['delay_days'] = (orders['order_delivered_customer_date'] - orders['order_estimated_delivery_date']).dt.total_seconds() / 86400.0
    orders['is_delayed'] = np.where(orders['order_delivered_customer_date'] > orders['order_estimated_delivery_date'], 1, 0)
    orders['order_purchase_year'] = orders['order_purchase_timestamp'].dt.year
    orders['order_purchase_month'] = orders['order_purchase_timestamp'].dt.to_period('M').astype(str)
    orders['order_purchase_dow'] = orders['order_purchase_timestamp'].dt.day_name()
    orders['order_purchase_hour'] = orders['order_purchase_timestamp'].dt.hour

    reviews_deduped = reviews.sort_values('review_answer_timestamp', ascending=False).drop_duplicates(subset=['order_id'])

    customers.to_csv(os.path.join(proc_dir, 'dim_customers.csv'), index=False)
    products.to_csv(os.path.join(proc_dir, 'dim_products.csv'), index=False)
    sellers.to_csv(os.path.join(proc_dir, 'dim_sellers.csv'), index=False)
    orders.to_csv(os.path.join(proc_dir, 'fact_orders.csv'), index=False)
    order_items.to_csv(os.path.join(proc_dir, 'fact_order_items.csv'), index=False)
    payments.to_csv(os.path.join(proc_dir, 'fact_order_payments.csv'), index=False)
    reviews_deduped.to_csv(os.path.join(proc_dir, 'fact_order_reviews.csv'), index=False)
    print("Cleaning & Transformation Complete!")

if __name__ == '__main__':
    run()
