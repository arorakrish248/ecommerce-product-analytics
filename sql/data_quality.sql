-- ==============================================================================
-- 01. DATA QUALITY & RECONCILIATION AUDIT (QUERIES 1 TO 5)
-- ==============================================================================

-- Q1: Total table volume and null rate analysis across core identifiers
SELECT 
    'fact_orders' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(order_id) AS non_null_keys,
    COUNT(DISTINCT order_id) AS distinct_keys,
    ROUND(100.0 * (COUNT(*) - COUNT(order_delivered_customer_date)) / COUNT(*), 2) AS pct_missing_delivery_date
FROM fact_orders
UNION ALL
SELECT 
    'dim_customers' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(customer_id) AS non_null_keys,
    COUNT(DISTINCT customer_unique_id) AS distinct_keys,
    ROUND(100.0 * (COUNT(*) - COUNT(customer_city)) / COUNT(*), 2) AS pct_missing_city
FROM dim_customers
UNION ALL
SELECT 
    'fact_order_items' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(order_id) AS non_null_keys,
    COUNT(DISTINCT product_id) AS distinct_keys,
    ROUND(100.0 * (COUNT(*) - COUNT(price)) / COUNT(*), 2) AS pct_missing_price
FROM fact_order_items;

-- Q2: Referential integrity check (Orphan orders or items)
SELECT 
    COUNT(i.order_id) AS total_items,
    COUNT(o.order_id) AS matched_orders,
    SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END) AS orphan_items
FROM fact_order_items i
LEFT JOIN fact_orders o ON i.order_id = o.order_id;

-- Q3: Impossible delivery dates and anomaly detection
SELECT 
    COUNT(*) AS total_delivered_orders,
    SUM(CASE WHEN order_delivered_customer_date < order_purchase_timestamp THEN 1 ELSE 0 END) AS impossible_delivery_dates,
    SUM(CASE WHEN order_approved_at < order_purchase_timestamp THEN 1 ELSE 0 END) AS impossible_approval_dates,
    ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
    ROUND(MIN(delivery_days), 2) AS min_delivery_days,
    ROUND(MAX(delivery_days), 2) AS max_delivery_days
FROM fact_orders
WHERE order_status = 'delivered';

-- Q4: Price and Freight Outlier & Distribution Check
SELECT 
    MIN(price) AS min_price,
    ROUND(AVG(price), 2) AS avg_price,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price) AS median_price,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY price) AS p95_price,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY price) AS p99_price,
    MAX(price) AS max_price,
    MIN(freight_value) AS min_freight,
    ROUND(AVG(freight_value), 2) AS avg_freight,
    MAX(freight_value) AS max_freight
FROM fact_order_items;

-- Q5: Payment value vs Item value reconciliation per order
WITH order_totals AS (
    SELECT 
        order_id,
        ROUND(SUM(price + freight_value), 2) AS item_total
    FROM fact_order_items
    GROUP BY order_id
),
payment_totals AS (
    SELECT 
        order_id,
        ROUND(SUM(payment_value), 2) AS payment_total
    FROM fact_order_payments
    GROUP BY order_id
)
SELECT 
    COUNT(*) AS reconciled_orders,
    SUM(CASE WHEN ABS(o.item_total - p.payment_total) < 0.01 THEN 1 ELSE 0 END) AS exact_matches,
    ROUND(100.0 * SUM(CASE WHEN ABS(o.item_total - p.payment_total) < 0.01 THEN 1 ELSE 0 END) / COUNT(*), 2) AS match_percentage
FROM order_totals o
JOIN payment_totals p ON o.order_id = p.order_id;
