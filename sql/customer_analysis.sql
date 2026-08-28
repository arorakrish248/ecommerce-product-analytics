-- ==============================================================================
-- 03. CUSTOMER ANALYTICS, COHORTS & RETENTION (QUERIES 11 TO 16)
-- ==============================================================================

-- Q11: Overall Customer Repeat Purchase Rate and Order Frequency Distribution
WITH customer_order_counts AS (
    SELECT 
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        ROUND(SUM(i.price + i.freight_value), 2) AS total_spend
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT 
    CASE 
        WHEN total_orders = 1 THEN '1 Order (One-and-Done)'
        WHEN total_orders = 2 THEN '2 Orders (Repeat Buyer)'
        WHEN total_orders BETWEEN 3 AND 5 THEN '3-5 Orders (Loyal Buyer)'
        ELSE '6+ Orders (Power Buyer)'
    END AS order_frequency_tier,
    COUNT(*) AS total_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS customer_pct,
    ROUND(SUM(total_spend), 2) AS total_gmv,
    ROUND(100.0 * SUM(total_spend) / SUM(SUM(total_spend)) OVER(), 2) AS gmv_pct,
    ROUND(AVG(total_spend), 2) AS avg_customer_spend
FROM customer_order_counts
GROUP BY 1
ORDER BY total_customers DESC;

-- Q12: 30 / 60 / 90 / 180-Day Repeat Purchase Windows
WITH ordered_customer_purchases AS (
    SELECT 
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_timestamp,
        ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) AS purchase_seq,
        LEAD(o.order_purchase_timestamp, 1) OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) AS next_purchase_timestamp
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
),
first_orders AS (
    SELECT 
        customer_unique_id,
        order_purchase_timestamp AS first_purchase_date,
        next_purchase_timestamp,
        DATE_DIFF('day', CAST(order_purchase_timestamp AS TIMESTAMP), CAST(next_purchase_timestamp AS TIMESTAMP)) AS days_to_second_order
    FROM ordered_customer_purchases
    WHERE purchase_seq = 1
)
SELECT 
    COUNT(*) AS total_acquired_customers,
    SUM(CASE WHEN next_purchase_timestamp IS NOT NULL THEN 1 ELSE 0 END) AS total_repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN next_purchase_timestamp IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS lifetime_repeat_rate_pct,
    SUM(CASE WHEN days_to_second_order <= 30 THEN 1 ELSE 0 END) AS repeat_within_30d,
    ROUND(100.0 * SUM(CASE WHEN days_to_second_order <= 30 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_30d_pct,
    SUM(CASE WHEN days_to_second_order <= 60 THEN 1 ELSE 0 END) AS repeat_within_60d,
    ROUND(100.0 * SUM(CASE WHEN days_to_second_order <= 60 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_60d_pct,
    SUM(CASE WHEN days_to_second_order <= 90 THEN 1 ELSE 0 END) AS repeat_within_90d,
    ROUND(100.0 * SUM(CASE WHEN days_to_second_order <= 90 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_90d_pct,
    SUM(CASE WHEN days_to_second_order <= 180 THEN 1 ELSE 0 END) AS repeat_within_180d,
    ROUND(100.0 * SUM(CASE WHEN days_to_second_order <= 180 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_180d_pct
FROM first_orders;

-- Q13: Monthly Customer Cohort Retention Analysis Matrix
WITH customer_first_cohort AS (
    SELECT 
        c.customer_unique_id,
        MIN(CAST(STRFTIME(CAST(o.order_purchase_timestamp AS TIMESTAMP), '%Y-%m') AS VARCHAR)) AS cohort_month
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
customer_activities AS (
    SELECT 
        c.customer_unique_id,
        CAST(STRFTIME(CAST(o.order_purchase_timestamp AS TIMESTAMP), '%Y-%m') AS VARCHAR) AS activity_month
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1, 2
),
cohort_size AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS num_cohort_users
    FROM customer_first_cohort
    GROUP BY cohort_month
),
retention_data AS (
    SELECT 
        f.cohort_month,
        a.activity_month,
        (CAST(SUBSTRING(a.activity_month, 1, 4) AS INT) - CAST(SUBSTRING(f.cohort_month, 1, 4) AS INT)) * 12 +
        (CAST(SUBSTRING(a.activity_month, 6, 2) AS INT) - CAST(SUBSTRING(f.cohort_month, 6, 2) AS INT)) AS month_index,
        COUNT(DISTINCT a.customer_unique_id) AS active_users
    FROM customer_first_cohort f
    JOIN customer_activities a ON f.customer_unique_id = a.customer_unique_id
    GROUP BY f.cohort_month, a.activity_month
)
SELECT 
    r.cohort_month,
    s.num_cohort_users AS cohort_size,
    r.month_index,
    r.active_users,
    ROUND(100.0 * r.active_users / s.num_cohort_users, 2) AS retention_rate_pct
FROM retention_data r
JOIN cohort_size s ON r.cohort_month = s.cohort_month
WHERE r.cohort_month >= '2017-01' AND r.cohort_month <= '2018-03' AND r.month_index BETWEEN 0 AND 6
ORDER BY r.cohort_month, r.month_index;

-- Q14: RFM (Recency, Frequency, Monetary) Customer Segmentation Model
WITH base_rfm AS (
    SELECT 
        c.customer_unique_id,
        DATE_DIFF('day', MAX(CAST(o.order_purchase_timestamp AS TIMESTAMP)), CAST('2018-10-18 00:00:00' AS TIMESTAMP)) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(i.price + i.freight_value), 2) AS monetary
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scores AS (
    SELECT 
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        CASE WHEN frequency = 1 THEN 1 WHEN frequency = 2 THEN 3 ELSE 5 END AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM base_rfm
),
rfm_segmented AS (
    SELECT 
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        r_score,
        f_score,
        m_score,
        CASE 
            WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions / VIP'
            WHEN r_score >= 3 AND f_score >= 2 THEN 'Loyal Potential'
            WHEN r_score >= 4 AND f_score = 1 THEN 'Recent New Customers'
            WHEN r_score = 3 AND f_score = 1 THEN 'Promising / Developing'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk / Need Attention'
            WHEN r_score <= 2 AND f_score = 2 THEN 'About to Churn'
            WHEN r_score = 1 AND f_score = 1 THEN 'Lost / Inactive'
            ELSE 'Standard Customers'
        END AS customer_segment
    FROM rfm_scores
)
SELECT 
    customer_segment,
    COUNT(*) AS total_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS customer_share_pct,
    ROUND(SUM(monetary), 2) AS total_gmv,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER(), 2) AS gmv_share_pct,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(frequency), 2) AS avg_frequency,
    ROUND(AVG(monetary), 2) AS avg_monetary_spend
FROM rfm_segmented
GROUP BY customer_segment
ORDER BY total_gmv DESC;

-- Q15: Customer Spend Concentration & Decile Pareto Analysis
WITH customer_spends AS (
    SELECT 
        c.customer_unique_id,
        ROUND(SUM(i.price + i.freight_value), 2) AS customer_spend
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
customer_deciles AS (
    SELECT 
        customer_unique_id,
        customer_spend,
        NTILE(10) OVER (ORDER BY customer_spend DESC) AS spend_decile
    FROM customer_spends
)
SELECT 
    spend_decile,
    COUNT(*) AS total_customers,
    ROUND(MIN(customer_spend), 2) AS min_decile_spend,
    ROUND(MAX(customer_spend), 2) AS max_decile_spend,
    ROUND(SUM(customer_spend), 2) AS decile_gmv,
    ROUND(100.0 * SUM(customer_spend) / SUM(SUM(customer_spend)) OVER(), 2) AS pct_of_total_gmv,
    ROUND(SUM(SUM(customer_spend)) OVER (ORDER BY spend_decile ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 / SUM(SUM(customer_spend)) OVER(), 2) AS cumulative_gmv_pct
FROM customer_deciles
GROUP BY spend_decile
ORDER BY spend_decile;

-- Q16: First Purchase Category Influence on Customer LTV & Repeat Likelihood
WITH customer_first_order AS (
    SELECT 
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_timestamp,
        ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) AS order_rank
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
),
first_order_details AS (
    SELECT 
        f.customer_unique_id,
        p.product_category_name_english AS entry_category
    FROM customer_first_order f
    JOIN fact_order_items i ON f.order_id = i.order_id
    JOIN dim_products p ON i.product_id = p.product_id
    WHERE f.order_rank = 1
    GROUP BY f.customer_unique_id, p.product_category_name_english
),
customer_lifetime_stats AS (
    SELECT 
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS lifetime_orders,
        ROUND(SUM(i.price + i.freight_value), 2) AS lifetime_gmv
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT 
    d.entry_category,
    COUNT(DISTINCT d.customer_unique_id) AS acquired_customers,
    SUM(CASE WHEN l.lifetime_orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN l.lifetime_orders > 1 THEN 1 ELSE 0 END) / COUNT(DISTINCT d.customer_unique_id), 2) AS repeat_rate_pct,
    ROUND(AVG(l.lifetime_gmv), 2) AS avg_customer_ltv
FROM first_order_details d
JOIN customer_lifetime_stats l ON d.customer_unique_id = l.customer_unique_id
GROUP BY d.entry_category
HAVING COUNT(DISTINCT d.customer_unique_id) >= 500
ORDER BY repeat_rate_pct DESC
LIMIT 15;
