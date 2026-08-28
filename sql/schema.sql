-- ==============================================================================
-- POSTGRESQL / RELATIONAL PRODUCTION SCHEMA DEFINITION
-- Enterprise Multi-Table E-Commerce Product Analytics Star/Snowflake Data Model
-- ==============================================================================

DROP TABLE IF EXISTS fact_order_reviews CASCADE;
DROP TABLE IF EXISTS fact_order_payments CASCADE;
DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS fact_orders CASCADE;
DROP TABLE IF EXISTS dim_sellers CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;

-- 1. Customers Dimension
CREATE TABLE dim_customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    customer_zip_code_prefix INT,
    customer_city VARCHAR(100),
    customer_state VARCHAR(5)
);

CREATE INDEX idx_dim_customers_unique_id ON dim_customers(customer_unique_id);
CREATE INDEX idx_dim_customers_state ON dim_customers(customer_state);

-- 2. Products Dimension
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

-- 3. Sellers Dimension
CREATE TABLE dim_sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix INT,
    seller_city VARCHAR(100),
    seller_state VARCHAR(5)
);

CREATE INDEX idx_dim_sellers_state ON dim_sellers(seller_state);

-- 4. Orders Core Fact Table
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

-- 5. Order Items Fact Table
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

-- 6. Order Payments Fact Table
CREATE TABLE fact_order_payments (
    order_id VARCHAR(32) REFERENCES fact_orders(order_id),
    payment_sequential INT,
    payment_type VARCHAR(20),
    payment_installments INT,
    payment_value NUMERIC(10,2)
);

CREATE INDEX idx_fact_order_payments_order_id ON fact_order_payments(order_id);
CREATE INDEX idx_fact_order_payments_type ON fact_order_payments(payment_type);

-- 7. Order Reviews Fact Table
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
