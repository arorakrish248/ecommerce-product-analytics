-- ==============================================================================
-- 02. EXPLORATORY & PERFORMANCE METRIC ANALYSIS (QUERIES 6 TO 10)
-- ==============================================================================

-- Q6: Monthly Orders, GMV, Net Items, and Active Buyer Trends (Growth Engine)
SELECT 
    o.order_purchase_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS active_buyers,
    ROUND(SUM(i.price), 2) AS total_item_gmv,
    ROUND(SUM(i.freight_value), 2) AS total_freight,
    ROUND(SUM(i.price + i.freight_value), 2) AS gross_merchandise_value,
    ROUND(AVG(i.price + i.freight_value), 2) AS avg_order_value
FROM fact_orders o
JOIN fact_order_items i ON o.order_id = i.order_id
WHERE o.order_status = 'delivered'
GROUP BY o.order_purchase_month
ORDER BY o.order_purchase_month;

-- Q7: Month-over-Month (MoM) GMV & Order Growth using Window Functions (LAG)
WITH monthly_metrics AS (
    SELECT 
        o.order_purchase_month,
        COUNT(DISTINCT o.order_id) AS monthly_orders,
        ROUND(SUM(i.price + i.freight_value), 2) AS monthly_gmv
    FROM fact_orders o
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY o.order_purchase_month
)
SELECT 
    order_purchase_month,
    monthly_orders,
    LAG(monthly_orders, 1) OVER (ORDER BY order_purchase_month) AS prev_month_orders,
    ROUND(100.0 * (monthly_orders - LAG(monthly_orders, 1) OVER (ORDER BY order_purchase_month)) / 
          NULLIF(LAG(monthly_orders, 1) OVER (ORDER BY order_purchase_month), 0), 2) AS order_growth_pct,
    monthly_gmv,
    LAG(monthly_gmv, 1) OVER (ORDER BY order_purchase_month) AS prev_month_gmv,
    ROUND(100.0 * (monthly_gmv - LAG(monthly_gmv, 1) OVER (ORDER BY order_purchase_month)) / 
          NULLIF(LAG(monthly_gmv, 1) OVER (ORDER BY order_purchase_month), 0), 2) AS gmv_growth_pct
FROM monthly_metrics
ORDER BY order_purchase_month;

-- Q8: Cumulative GMV and 3-Month Moving Average of GMV
WITH monthly_revenue AS (
    SELECT 
        o.order_purchase_month,
        ROUND(SUM(i.price + i.freight_value), 2) AS gmv
    FROM fact_orders o
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY o.order_purchase_month
)
SELECT 
    order_purchase_month,
    gmv,
    ROUND(SUM(gmv) OVER (ORDER BY order_purchase_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_gmv,
    ROUND(AVG(gmv) OVER (ORDER BY order_purchase_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS gmv_3m_moving_avg
FROM monthly_revenue
ORDER BY order_purchase_month;

-- Q9: Hourly & Day-of-Week Conversion Purchase Heatmap
SELECT 
    order_purchase_dow,
    order_purchase_hour,
    COUNT(order_id) AS total_orders,
    ROUND(AVG(delivery_days), 2) AS avg_delivery_days
FROM fact_orders
WHERE order_status = 'delivered'
GROUP BY order_purchase_dow, order_purchase_hour
ORDER BY total_orders DESC
LIMIT 20;

-- Q10: Payment Method Mix, Installment Distribution & Ticket Size
SELECT 
    payment_type,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(100.0 * COUNT(DISTINCT order_id) / SUM(COUNT(DISTINCT order_id)) OVER(), 2) AS payment_share_pct,
    ROUND(SUM(payment_value), 2) AS total_payment_value,
    ROUND(AVG(payment_value), 2) AS avg_ticket_size,
    ROUND(AVG(payment_installments), 2) AS avg_installments,
    MAX(payment_installments) AS max_installments
FROM fact_order_payments
GROUP BY payment_type
ORDER BY total_payment_value DESC;
