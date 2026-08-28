-- ==============================================================================
-- PART 1: RE-CREATE TABLES WITH NUMERIC/DECIMAL TOLERANT TYPES
-- ==============================================================================

DROP TABLE IF EXISTS fact_order_reviews CASCADE;
DROP TABLE IF EXISTS fact_order_payments CASCADE;
DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS fact_orders CASCADE;
DROP TABLE IF EXISTS dim_sellers CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;

CREATE TABLE dim_customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    customer_zip_code_prefix INT,
    customer_city VARCHAR(100),
    customer_state VARCHAR(5)
);

CREATE TABLE dim_products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght NUMERIC(10,2),
    product_description_lenght NUMERIC(10,2),
    product_photos_qty NUMERIC(10,2),
    product_weight_g NUMERIC(10,2),
    product_length_cm NUMERIC(10,2),
    product_height_cm NUMERIC(10,2),
    product_width_cm NUMERIC(10,2),
    product_category_name_english VARCHAR(100)
);

CREATE TABLE dim_sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix INT,
    seller_city VARCHAR(100),
    seller_state VARCHAR(5)
);

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

CREATE TABLE fact_order_payments (
    order_id VARCHAR(32) REFERENCES fact_orders(order_id),
    payment_sequential INT,
    payment_type VARCHAR(20),
    payment_installments INT,
    payment_value NUMERIC(10,2)
);

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
