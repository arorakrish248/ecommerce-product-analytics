-- ==============================================================================
-- PART 2: IMPORT DATA
-- Run this AFTER running Step 1!
-- ==============================================================================

COPY dim_customers FROM 'C:/Users/Public/ecommerce_analytics_data/dim_customers.csv' WITH (FORMAT csv, HEADER true);
COPY dim_products FROM 'C:/Users/Public/ecommerce_analytics_data/dim_products.csv' WITH (FORMAT csv, HEADER true);
COPY dim_sellers FROM 'C:/Users/Public/ecommerce_analytics_data/dim_sellers.csv' WITH (FORMAT csv, HEADER true);
COPY fact_orders FROM 'C:/Users/Public/ecommerce_analytics_data/fact_orders.csv' WITH (FORMAT csv, HEADER true);
COPY fact_order_items FROM 'C:/Users/Public/ecommerce_analytics_data/fact_order_items.csv' WITH (FORMAT csv, HEADER true);
COPY fact_order_payments FROM 'C:/Users/Public/ecommerce_analytics_data/fact_order_payments.csv' WITH (FORMAT csv, HEADER true);
COPY fact_order_reviews FROM 'C:/Users/Public/ecommerce_analytics_data/fact_order_reviews.csv' WITH (FORMAT csv, HEADER true);

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
