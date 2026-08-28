-- ==============================================================================
-- 05. BUSINESS OPERATIONS, LOGISTICS & GEOGRAPHY (QUERIES 22 TO 27)
-- ==============================================================================

-- Q22: On-Time vs Delayed Delivery Impact on Customer Review Scores
SELECT 
    CASE 
        WHEN is_delayed = 1 THEN 'Delayed Delivery'
        ELSE 'On-Time / Ahead of Schedule'
    END AS delivery_performance,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(100.0 * COUNT(DISTINCT o.order_id) / SUM(COUNT(DISTINCT o.order_id)) OVER(), 2) AS order_share_pct,
    ROUND(AVG(o.delivery_days), 2) AS avg_delivery_days,
    ROUND(AVG(r.review_score), 2) AS avg_csat_score,
    ROUND(100.0 * SUM(CASE WHEN r.review_score = 5 THEN 1 ELSE 0 END) / COUNT(r.review_score), 2) AS pct_5_star_reviews,
    ROUND(100.0 * SUM(CASE WHEN r.review_score = 1 THEN 1 ELSE 0 END) / COUNT(r.review_score), 2) AS pct_1_star_reviews
FROM fact_orders o
JOIN fact_order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY is_delayed;

-- Q23: Delivery Delay Magnitude vs Review Score Degradation Curve
SELECT 
    CASE 
        WHEN delay_days <= -7 THEN 'Delivered >7 Days Early'
        WHEN delay_days BETWEEN -6.99 AND -1 THEN 'Delivered 1-7 Days Early'
        WHEN delay_days BETWEEN -0.99 AND 0 THEN 'Delivered On Estimated Day'
        WHEN delay_days BETWEEN 0.01 AND 3 THEN 'Delayed 1-3 Days'
        WHEN delay_days BETWEEN 3.01 AND 7 THEN 'Delayed 4-7 Days'
        WHEN delay_days BETWEEN 7.01 AND 14 THEN 'Delayed 8-14 Days'
        ELSE 'Delayed >14 Days (Critical Failure)'
    END AS delivery_time_bracket,
    COUNT(*) AS total_orders,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(100.0 * SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS negative_sentiment_rate
FROM fact_orders o
JOIN fact_order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY avg_review_score DESC;

-- Q24: Geographic Performance: State-Level GMV, Average Delivery Days & Delay Rates
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(i.price + i.freight_value), 2) AS state_gmv,
    ROUND(AVG(i.price + i.freight_value), 2) AS avg_order_value,
    ROUND(AVG(o.delivery_days), 2) AS avg_delivery_days,
    ROUND(AVG(o.estimated_days), 2) AS avg_promised_days,
    ROUND(100.0 * SUM(o.is_delayed) / COUNT(o.order_id), 2) AS delay_rate_pct,
    ROUND(AVG(r.review_score), 2) AS avg_state_csat
FROM dim_customers c
JOIN fact_orders o ON c.customer_id = o.customer_id
JOIN fact_order_items i ON o.order_id = i.order_id
LEFT JOIN fact_order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY state_gmv DESC;

-- Q25: Intra-State vs Inter-State Logistics Friction
SELECT 
    CASE 
        WHEN c.customer_state = s.seller_state THEN 'Intra-State (Same State Shipping)'
        ELSE 'Inter-State (Cross-State Shipping)'
    END AS shipping_corridor_type,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(AVG(i.freight_value), 2) AS avg_freight_cost,
    ROUND(AVG(o.delivery_days), 2) AS avg_delivery_days,
    ROUND(100.0 * SUM(o.is_delayed) / COUNT(DISTINCT o.order_id), 2) AS delay_rate_pct,
    ROUND(AVG(r.review_score), 2) AS avg_customer_rating
FROM fact_orders o
JOIN fact_order_items i ON o.order_id = i.order_id
JOIN dim_customers c ON o.customer_id = c.customer_id
JOIN dim_sellers s ON i.seller_id = s.seller_id
LEFT JOIN fact_order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1;

-- Q26: Seller Performance, Delivery Reliability & Rating Deciles
WITH seller_metrics AS (
    SELECT 
        s.seller_id,
        s.seller_state,
        COUNT(DISTINCT i.order_id) AS total_orders_fulfilled,
        ROUND(SUM(i.price), 2) AS seller_revenue,
        ROUND(AVG(o.carrier_handling_days), 2) AS avg_fulfillment_days,
        ROUND(100.0 * SUM(o.is_delayed) / COUNT(DISTINCT i.order_id), 2) AS delay_rate_pct,
        ROUND(AVG(r.review_score), 2) AS avg_seller_rating
    FROM dim_sellers s
    JOIN fact_order_items i ON s.seller_id = i.seller_id
    JOIN fact_orders o ON i.order_id = o.order_id
    LEFT JOIN fact_order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY s.seller_id, s.seller_state
    HAVING COUNT(DISTINCT i.order_id) >= 30
)
SELECT 
    seller_state,
    COUNT(seller_id) AS qualified_sellers,
    ROUND(AVG(total_orders_fulfilled), 1) AS avg_orders_per_seller,
    ROUND(AVG(seller_revenue), 2) AS avg_revenue_per_seller,
    ROUND(AVG(avg_fulfillment_days), 2) AS avg_fulfillment_days,
    ROUND(AVG(delay_rate_pct), 2) AS avg_delay_rate,
    ROUND(AVG(avg_seller_rating), 2) AS avg_satisfaction_score
FROM seller_metrics
GROUP BY seller_state
HAVING COUNT(seller_id) >= 10
ORDER BY avg_revenue_per_seller DESC;

-- Q27: Funnel & Order Cancellation Diagnostics
SELECT 
    order_status,
    COUNT(*) AS total_orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS status_share_pct,
    ROUND(AVG(CASE WHEN order_status = 'delivered' THEN delivery_days ELSE NULL END), 2) AS avg_delivery_days
FROM fact_orders
GROUP BY order_status
ORDER BY total_orders DESC;
