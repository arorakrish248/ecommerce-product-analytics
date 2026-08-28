import duckdb

con = duckdb.connect('data/processed/ecommerce_analytics.duckdb')
print("=== EXACT VERIFIED AUDIT NUMBERS ===")

# 1. Total Volume
tot_orders = con.execute("SELECT count(distinct order_id) FROM fact_orders").fetchone()[0]
delivered_orders = con.execute("SELECT count(distinct order_id) FROM fact_orders WHERE order_status = 'delivered'").fetchone()[0]
tot_customers = con.execute("SELECT count(distinct customer_unique_id) FROM dim_customers").fetchone()[0]
tot_gmv = con.execute("SELECT round(sum(price + freight_value), 2) FROM fact_order_items i JOIN fact_orders o ON i.order_id=o.order_id WHERE o.order_status='delivered'").fetchone()[0]

print(f"Total Orders: {tot_orders:,}")
print(f"Delivered Orders: {delivered_orders:,}")
print(f"Total Unique Customers: {tot_customers:,}")
print(f"Total Platform GMV: ${tot_gmv:,.2f}")

# 2. Repeat Rate
repeat_res = con.execute("""
    WITH cust_orders AS (
        SELECT c.customer_unique_id, count(distinct o.order_id) as orders
        FROM dim_customers c
        JOIN fact_orders o ON c.customer_id = o.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id
    )
    SELECT 
        count(*) as total_buyers,
        sum(case when orders > 1 then 1 else 0 end) as repeat_buyers,
        round(100.0 * sum(case when orders > 1 then 1 else 0 end) / count(*), 2) as repeat_rate_pct
    FROM cust_orders
""").fetchone()
print(f"Repeat Buyers: {repeat_res[1]:,} / {repeat_res[0]:,} ({repeat_res[2]}%)")

# 3. Delivery Delay vs CSAT
delay_res = con.execute("""
    SELECT 
        is_delayed,
        count(distinct o.order_id) as orders,
        round(avg(r.review_score), 2) as avg_csat,
        round(100.0 * sum(case when r.review_score <= 2 then 1 else 0 end) / count(*), 2) as detractor_pct
    FROM fact_orders o
    JOIN fact_order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY is_delayed
""").fetchall()
print("Delivery Delay Breakdown (0=On-time, 1=Delayed):", delay_res)

# 4. Intra-state vs Inter-state
corridor_res = con.execute("""
    SELECT 
        case when c.customer_state = s.seller_state then 'Intra-State' else 'Inter-State' end as corridor,
        count(distinct o.order_id) as orders,
        round(avg(o.delivery_days), 1) as avg_days,
        round(100.0 * sum(o.is_delayed) / count(distinct o.order_id), 1) as delay_pct
    FROM fact_orders o
    JOIN fact_order_items i ON o.order_id = i.order_id
    JOIN dim_customers c ON o.customer_id = c.customer_id
    JOIN dim_sellers s ON i.seller_id = s.seller_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
""").fetchall()
print("Corridor Friction:", corridor_res)

# 5. Top 3 Categories
top_cats = con.execute("""
    SELECT 
        p.product_category_name_english as cat,
        round(sum(i.price + i.freight_value), 2) as gmv,
        round(100.0 * sum(i.price + i.freight_value) / 15421083.0, 1) as gmv_share
    FROM fact_order_items i
    JOIN dim_products p ON i.product_id = p.product_id
    JOIN fact_orders o ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
    ORDER BY gmv DESC
    LIMIT 5
""").fetchall()
print("Top 5 Categories:", top_cats)
con.close()
