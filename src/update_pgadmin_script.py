import os

proc_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/processed'.replace('\\', '/')

sql_header = f"""-- ==============================================================================
-- 🚀 ONE-CLICK PGADMIN MASTER SETUP SCRIPT
-- ==============================================================================
-- The data files are already downloaded and processed on your computer at:
-- {proc_dir}/
--
-- Running this script imports the data locally into your pgAdmin database!
-- ==============================================================================

-- 1. CLEAN UP PREVIOUS TABLES
DROP TABLE IF EXISTS fact_order_reviews CASCADE;
DROP TABLE IF EXISTS fact_order_payments CASCADE;
DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS fact_orders CASCADE;
DROP TABLE IF EXISTS dim_sellers CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;

-- 2. CREATE DIMENSION & FACT TABLES
CREATE TABLE dim_customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    customer_zip_code_prefix INT,
    customer_city VARCHAR(100),
    customer_state VARCHAR(5)
);
CREATE INDEX idx_dim_customers_unique_id ON dim_customers(customer_unique_id);
CREATE INDEX idx_dim_customers_state ON dim_customers(customer_state);

CREATE TABLE dim_products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g NUMERIC(10,2),
    product_length_cm NUMERIC(10,2),
    product_height_cm NUMERIC(10,2),
    product_width_cm NUMERIC(10,2),
    product_category_name_english VARCHAR(100)
);
CREATE INDEX idx_dim_products_category ON dim_products(product_category_name_english);

CREATE TABLE dim_sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix INT,
    seller_city VARCHAR(100),
    seller_state VARCHAR(5)
);
CREATE INDEX idx_dim_sellers_state ON dim_sellers(seller_state);

CREATE TABLE fact_orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) REFERENCES dim_customers(customer_id),
    order_status VARCHAR(20),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    delivery_days NUMERIC(10,2),
    estimated_days NUMERIC(10,2),
    carrier_handling_days NUMERIC(10,2),
    transit_days NUMERIC(10,2),
    delay_days NUMERIC(10,2),
    is_delayed INT,
    order_purchase_year INT,
    order_purchase_month VARCHAR(10),
    order_purchase_dow VARCHAR(15),
    order_purchase_hour INT
);
CREATE INDEX idx_fact_orders_customer_id ON fact_orders(customer_id);
CREATE INDEX idx_fact_orders_purchase_timestamp ON fact_orders(order_purchase_timestamp);
CREATE INDEX idx_fact_orders_status ON fact_orders(order_status);

CREATE TABLE fact_order_items (
    order_id VARCHAR(32) REFERENCES fact_orders(order_id),
    order_item_id INT,
    product_id VARCHAR(32) REFERENCES dim_products(product_id),
    seller_id VARCHAR(32) REFERENCES dim_sellers(seller_id),
    shipping_limit_date TIMESTAMP,
    price NUMERIC(10,2),
    freight_value NUMERIC(10,2),
    PRIMARY KEY (order_id, order_item_id)
);
CREATE INDEX idx_fact_order_items_product ON fact_order_items(product_id);
CREATE INDEX idx_fact_order_items_seller ON fact_order_items(seller_id);

CREATE TABLE fact_order_payments (
    order_id VARCHAR(32) REFERENCES fact_orders(order_id),
    payment_sequential INT,
    payment_type VARCHAR(20),
    payment_installments INT,
    payment_value NUMERIC(10,2)
);
CREATE INDEX idx_fact_order_payments_order_id ON fact_order_payments(order_id);
CREATE INDEX idx_fact_order_payments_type ON fact_order_payments(payment_type);

CREATE TABLE fact_order_reviews (
    review_id VARCHAR(32),
    order_id VARCHAR(32) REFERENCES fact_orders(order_id),
    review_score INT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);
CREATE INDEX idx_fact_order_reviews_order_id ON fact_order_reviews(order_id);
CREATE INDEX idx_fact_order_reviews_score ON fact_order_reviews(review_score);

-- 3. BULK IMPORT FROM LOCAL DISK
-- PostgreSQL server reads directly from your local processed files:
COPY dim_customers FROM '{proc_dir}/dim_customers.csv' WITH (FORMAT csv, HEADER true);
COPY dim_products FROM '{proc_dir}/dim_products.csv' WITH (FORMAT csv, HEADER true);
COPY dim_sellers FROM '{proc_dir}/dim_sellers.csv' WITH (FORMAT csv, HEADER true);
COPY fact_orders FROM '{proc_dir}/fact_orders.csv' WITH (FORMAT csv, HEADER true);
COPY fact_order_items FROM '{proc_dir}/fact_order_items.csv' WITH (FORMAT csv, HEADER true);
COPY fact_order_payments FROM '{proc_dir}/fact_order_payments.csv' WITH (FORMAT csv, HEADER true);
COPY fact_order_reviews FROM '{proc_dir}/fact_order_reviews.csv' WITH (FORMAT csv, HEADER true);

-- 4. VALIDATION QUERY (Check row counts)
SELECT 'dim_customers' AS table_name, count(*) AS total_rows FROM dim_customers
UNION ALL
SELECT 'dim_products' AS table_name, count(*) AS total_rows FROM dim_products
UNION ALL
SELECT 'dim_sellers' AS table_name, count(*) AS total_rows FROM dim_sellers
UNION ALL
SELECT 'fact_orders' AS table_name, count(*) AS total_rows FROM fact_orders
UNION ALL
SELECT 'fact_order_items' AS table_name, count(*) AS total_rows FROM fact_order_items
UNION ALL
SELECT 'fact_order_payments' AS table_name, count(*) AS total_rows FROM fact_order_payments
UNION ALL
SELECT 'fact_order_reviews' AS table_name, count(*) AS total_rows FROM fact_order_reviews;
"""

with open('sql/RUN_IN_PGADMIN.sql', 'w', encoding='utf-8') as f:
    f.write(sql_header)

print("Updated sql/RUN_IN_PGADMIN.sql with clear file path references.")
