-- ==============================================================================
-- 04. PRODUCT, CATEGORY & CROSS-SELLING ANALYTICS (QUERIES 17 TO 21)
-- ==============================================================================

-- Q17: Top 15 Product Categories by GMV, Units Sold, and Average Price
SELECT 
    p.product_category_name_english AS category,
    COUNT(DISTINCT i.order_id) AS total_orders,
    COUNT(i.order_item_id) AS units_sold,
    ROUND(SUM(i.price), 2) AS item_revenue,
    ROUND(SUM(i.freight_value), 2) AS freight_revenue,
    ROUND(SUM(i.price + i.freight_value), 2) AS total_gmv,
    ROUND(AVG(i.price), 2) AS avg_item_price,
    ROUND(AVG(i.freight_value), 2) AS avg_freight_cost
FROM fact_order_items i
JOIN dim_products p ON i.product_id = p.product_id
JOIN fact_orders o ON i.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.product_category_name_english
ORDER BY total_gmv DESC
LIMIT 15;

-- Q18: Category Growth Matrix (Comparing 2017 vs 2018 Performance)
WITH category_yearly AS (
    SELECT 
        p.product_category_name_english AS category,
        o.order_purchase_year,
        ROUND(SUM(i.price + i.freight_value), 2) AS gmv
    FROM fact_order_items i
    JOIN dim_products p ON i.product_id = p.product_id
    JOIN fact_orders o ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered' AND o.order_purchase_year IN (2017, 2018)
    GROUP BY p.product_category_name_english, o.order_purchase_year
)
SELECT 
    category,
    SUM(CASE WHEN order_purchase_year = 2017 THEN gmv ELSE 0 END) AS gmv_2017,
    SUM(CASE WHEN order_purchase_year = 2018 THEN gmv ELSE 0 END) AS gmv_2018,
    ROUND(100.0 * (SUM(CASE WHEN order_purchase_year = 2018 THEN gmv ELSE 0 END) - SUM(CASE WHEN order_purchase_year = 2017 THEN gmv ELSE 0 END)) / 
          NULLIF(SUM(CASE WHEN order_purchase_year = 2017 THEN gmv ELSE 0 END), 0), 2) AS yoy_growth_pct
FROM category_yearly
GROUP BY category
HAVING SUM(CASE WHEN order_purchase_year = 2017 THEN gmv ELSE 0 END) >= 50000
ORDER BY gmv_2018 DESC
LIMIT 15;

-- Q19: Product Concentration & Top Product Pareto Distribution
WITH product_gmv AS (
    SELECT 
        i.product_id,
        p.product_category_name_english AS category,
        COUNT(i.order_item_id) AS total_units_sold,
        ROUND(SUM(i.price + i.freight_value), 2) AS product_total_gmv
    FROM fact_order_items i
    JOIN dim_products p ON i.product_id = p.product_id
    JOIN fact_orders o ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY i.product_id, p.product_category_name_english
),
ranked_products AS (
    SELECT 
        product_id,
        category,
        total_units_sold,
        product_total_gmv,
        ROW_NUMBER() OVER (ORDER BY product_total_gmv DESC) AS rank_order,
        SUM(product_total_gmv) OVER (ORDER BY product_total_gmv DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_gmv,
        SUM(product_total_gmv) OVER () AS total_platform_gmv
    FROM product_gmv
)
SELECT 
    rank_order,
    product_id,
    category,
    total_units_sold,
    product_total_gmv,
    ROUND(100.0 * cumulative_gmv / total_platform_gmv, 2) AS cumulative_gmv_pct
FROM ranked_products
WHERE rank_order IN (1, 10, 50, 100, 500, 1000, 2000, 5000, 10000, 30000);

-- Q20: High-Volume Products with Substandard Review Scores (Quality Risk)
SELECT 
    p.product_id,
    p.product_category_name_english AS category,
    COUNT(DISTINCT i.order_id) AS order_volume,
    ROUND(SUM(i.price + i.freight_value), 2) AS total_gmv,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(100.0 * SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) / COUNT(r.review_score), 2) AS negative_review_pct
FROM fact_order_items i
JOIN dim_products p ON i.product_id = p.product_id
JOIN fact_orders o ON i.order_id = o.order_id
JOIN fact_order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.product_id, p.product_category_name_english
HAVING COUNT(DISTINCT i.order_id) >= 50 AND AVG(r.review_score) < 3.5
ORDER BY total_gmv DESC
LIMIT 15;

-- Q21: Market Basket / Co-Purchasing Affinity (Pairs Bought in Same Multi-Item Order)
WITH multi_item_orders AS (
    SELECT 
        i1.order_id,
        p1.product_category_name_english AS category_a,
        p2.product_category_name_english AS category_b
    FROM fact_order_items i1
    JOIN fact_order_items i2 ON i1.order_id = i2.order_id AND i1.product_id < i2.product_id
    JOIN dim_products p1 ON i1.product_id = p1.product_id
    JOIN dim_products p2 ON i2.product_id = p2.product_id
    JOIN fact_orders o ON i1.order_id = o.order_id
    WHERE o.order_status = 'delivered' AND p1.product_category_name_english <> p2.product_category_name_english
)
SELECT 
    category_a,
    category_b,
    COUNT(*) AS co_purchase_frequency
FROM multi_item_orders
GROUP BY category_a, category_b
ORDER BY co_purchase_frequency DESC
LIMIT 15;
