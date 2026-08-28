import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import duckdb
import os

charts_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/reports/charts'
os.makedirs(charts_dir, exist_ok=True)
db_path = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/processed/ecommerce_analytics.duckdb'
con = duckdb.connect(db_path)

print("Starting Fast Headless Plotting...")

# Chart 1: Monthly Growth
df_growth = con.execute("""
    SELECT 
        order_purchase_month,
        COUNT(DISTINCT o.order_id) AS orders,
        ROUND(SUM(i.price + i.freight_value), 2) AS gmv
    FROM fact_orders o
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered' AND order_purchase_month >= '2017-01' AND order_purchase_month <= '2018-08'
    GROUP BY order_purchase_month
    ORDER BY order_purchase_month
""").fetchdf()

fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.bar(df_growth['order_purchase_month'], df_growth['orders'], color='#1f77b4', alpha=0.7, width=0.6)
ax1.set_ylabel('Delivered Orders', color='#1f77b4', fontsize=12, fontweight='bold')
ax1.tick_params(axis='x', rotation=45)
ax2 = ax1.twinx()
ax2.plot(df_growth['order_purchase_month'], df_growth['gmv'], color='#d62728', marker='o', linewidth=2.5)
ax2.set_ylabel('GMV ($)', color='#d62728', fontsize=12, fontweight='bold')
plt.title('Platform Growth Engine: Monthly Orders & GMV (2017-2018)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/01_monthly_growth_trajectory.png', dpi=150)
plt.close()
print("Saved Chart 1")

# Chart 2: Cohort Heatmap
df_cohort = con.execute("""
    WITH customer_first_cohort AS (
        SELECT c.customer_unique_id, MIN(CAST(STRFTIME(CAST(o.order_purchase_timestamp AS TIMESTAMP), '%Y-%m') AS VARCHAR)) AS cohort_month
        FROM dim_customers c JOIN fact_orders o ON c.customer_id = o.customer_id WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id
    ),
    customer_activities AS (
        SELECT c.customer_unique_id, CAST(STRFTIME(CAST(o.order_purchase_timestamp AS TIMESTAMP), '%Y-%m') AS VARCHAR) AS activity_month
        FROM dim_customers c JOIN fact_orders o ON c.customer_id = o.customer_id WHERE o.order_status = 'delivered'
        GROUP BY 1, 2
    ),
    cohort_size AS (SELECT cohort_month, COUNT(DISTINCT customer_unique_id) AS num_users FROM customer_first_cohort GROUP BY cohort_month),
    retention_data AS (
        SELECT f.cohort_month,
            (CAST(SUBSTRING(a.activity_month, 1, 4) AS INT) - CAST(SUBSTRING(f.cohort_month, 1, 4) AS INT)) * 12 +
            (CAST(SUBSTRING(a.activity_month, 6, 2) AS INT) - CAST(SUBSTRING(f.cohort_month, 6, 2) AS INT)) AS month_index,
            COUNT(DISTINCT a.customer_unique_id) AS active_users
        FROM customer_first_cohort f JOIN customer_activities a ON f.customer_unique_id = a.customer_unique_id
        GROUP BY f.cohort_month, month_index
    )
    SELECT r.cohort_month, s.num_users, r.month_index, ROUND(100.0 * r.active_users / s.num_users, 2) AS retention_pct
    FROM retention_data r JOIN cohort_size s ON r.cohort_month = s.cohort_month
    WHERE r.cohort_month >= '2017-01' AND r.cohort_month <= '2018-03' AND r.month_index BETWEEN 0 AND 6
    ORDER BY r.cohort_month, r.month_index
""").fetchdf()

pivot_retention = df_cohort.pivot(index='cohort_month', columns='month_index', values='retention_pct')
plt.figure(figsize=(10, 6))
sns.heatmap(pivot_retention, annot=True, fmt='.2f', cmap='YlGnBu', cbar_kws={'label': 'Retention %'}, vmin=0, vmax=1.5)
plt.title('Monthly Customer Cohort Retention Heatmap', fontsize=13, fontweight='bold')
plt.xlabel('Cohort Month Index', fontweight='bold')
plt.ylabel('Acquisition Cohort', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/02_cohort_retention_heatmap.png', dpi=150)
plt.close()
print("Saved Chart 2")

# Chart 3: RFM Customer Segments
df_rfm = con.execute("""
    WITH base_rfm AS (
        SELECT c.customer_unique_id,
            DATE_DIFF('day', MAX(CAST(o.order_purchase_timestamp AS TIMESTAMP)), CAST('2018-10-18 00:00:00' AS TIMESTAMP)) AS recency_days,
            COUNT(DISTINCT o.order_id) AS frequency,
            ROUND(SUM(i.price + i.freight_value), 2) AS monetary
        FROM dim_customers c JOIN fact_orders o ON c.customer_id = o.customer_id JOIN fact_order_items i ON o.order_id = i.order_id
        WHERE o.order_status = 'delivered' GROUP BY c.customer_unique_id
    ),
    rfm_scores AS (
        SELECT customer_unique_id, recency_days, frequency, monetary,
            NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
            CASE WHEN frequency = 1 THEN 1 WHEN frequency = 2 THEN 3 ELSE 5 END AS f_score,
            NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
        FROM base_rfm
    ),
    rfm_segmented AS (
        SELECT customer_unique_id,
            CASE 
                WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions / VIP'
                WHEN r_score >= 3 AND f_score >= 2 THEN 'Loyal Potential'
                WHEN r_score >= 4 AND f_score = 1 THEN 'Recent New Customers'
                WHEN r_score = 3 AND f_score = 1 THEN 'Promising / Developing'
                WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk / Need Attention'
                WHEN r_score <= 2 AND f_score = 2 THEN 'About to Churn'
                WHEN r_score = 1 AND f_score = 1 THEN 'Lost / Inactive'
                ELSE 'Standard Customers'
            END AS customer_segment, monetary
        FROM rfm_scores
    )
    SELECT customer_segment, COUNT(*) AS total_customers, ROUND(SUM(monetary), 2) AS total_gmv
    FROM rfm_segmented GROUP BY customer_segment ORDER BY total_gmv DESC
""").fetchdf()

plt.figure(figsize=(11, 5.5))
plt.barh(df_rfm['customer_segment'], df_rfm['total_gmv'] / 1e6, color='#2ca02c', alpha=0.8)
plt.xlabel('Total GMV ($ Millions)', fontweight='bold')
plt.title('Customer Segment GMV Breakdown (RFM Framework)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/03_rfm_customer_segments.png', dpi=150)
plt.close()
print("Saved Chart 3")

# Chart 4: Delay vs CSAT
df_delay = con.execute("""
    SELECT 
        CASE 
            WHEN delay_days <= -7 THEN 'Early >7d'
            WHEN delay_days BETWEEN -6.99 AND -1 THEN 'Early 1-7d'
            WHEN delay_days BETWEEN -0.99 AND 0 THEN 'On-Time'
            WHEN delay_days BETWEEN 0.01 AND 3 THEN 'Delayed 1-3d'
            WHEN delay_days BETWEEN 3.01 AND 7 THEN 'Delayed 4-7d'
            WHEN delay_days BETWEEN 7.01 AND 14 THEN 'Delayed 8-14d'
            ELSE 'Delayed >14d'
        END AS delivery_bracket,
        ROUND(AVG(r.review_score), 2) AS avg_csat,
        ROUND(100.0 * SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS negative_pct
    FROM fact_orders o JOIN fact_order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered' GROUP BY 1
""").fetchdf()

bracket_order = ['Early >7d', 'Early 1-7d', 'On-Time', 'Delayed 1-3d', 'Delayed 4-7d', 'Delayed 8-14d', 'Delayed >14d']
df_delay['rank'] = df_delay['delivery_bracket'].apply(lambda x: bracket_order.index(x) if x in bracket_order else 99)
df_delay = df_delay.sort_values('rank')

fig, ax1 = plt.subplots(figsize=(10, 5.5))
ax1.plot(df_delay['delivery_bracket'], df_delay['avg_csat'], color='#2ca02c', marker='o', linewidth=3)
ax1.set_ylabel('Avg Rating (1-5)', color='#2ca02c', fontweight='bold')
ax1.set_ylim(1, 5)
ax1.tick_params(axis='x', rotation=30)
ax2 = ax1.twinx()
ax2.bar(df_delay['delivery_bracket'], df_delay['negative_pct'], color='#d62728', alpha=0.35, width=0.4)
ax2.set_ylabel('% Detractors (1-2 Stars)', color='#d62728', fontweight='bold')
ax2.set_ylim(0, 100)
plt.title('The Experience Cliff: Delivery Delay vs CSAT Rating', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/04_delay_vs_csat_degradation.png', dpi=150)
plt.close()
print("Saved Chart 4")

# Chart 5: Category CSAT vs GMV
df_cat = con.execute("""
    SELECT p.product_category_name_english AS category, ROUND(SUM(i.price + i.freight_value), 2) AS total_gmv, ROUND(AVG(r.review_score), 2) AS avg_csat
    FROM fact_order_items i JOIN dim_products p ON i.product_id = p.product_id JOIN fact_orders o ON i.order_id = o.order_id JOIN fact_order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered' GROUP BY 1 ORDER BY total_gmv DESC LIMIT 12
""").fetchdf()

plt.figure(figsize=(11, 5.5))
plt.scatter(df_cat['total_gmv']/1e6, df_cat['avg_csat'], s=250, color='#3b528b', alpha=0.8, edgecolors='black')
for _, row in df_cat.iterrows():
    plt.annotate(row['category'], (row['total_gmv']/1e6 + 0.02, row['avg_csat'] + 0.01), fontsize=8.5, fontweight='bold')
plt.axhline(4.0, color='red', linestyle='--', alpha=0.7)
plt.title('Top Product Categories: Revenue Volume vs CSAT Score', fontsize=13, fontweight='bold')
plt.xlabel('Category GMV ($ Millions)', fontweight='bold')
plt.ylabel('Avg Rating (1-5)', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/05_category_revenue_vs_satisfaction.png', dpi=150)
plt.close()
print("Saved Chart 5")

# Chart 6: Geography Disparity
df_geo = con.execute("""
    SELECT c.customer_state, ROUND(AVG(o.delivery_days), 1) AS avg_delivery_days, ROUND(100.0 * SUM(o.is_delayed) / COUNT(o.order_id), 1) AS delay_rate_pct
    FROM dim_customers c JOIN fact_orders o ON c.customer_id = o.customer_id WHERE o.order_status = 'delivered'
    GROUP BY 1 HAVING COUNT(DISTINCT o.order_id) >= 800 ORDER BY avg_delivery_days ASC
""").fetchdf()

fig, ax1 = plt.subplots(figsize=(11, 5.5))
ax1.bar(df_geo['customer_state'], df_geo['avg_delivery_days'], color='#440154', alpha=0.75)
ax1.set_ylabel('Avg Delivery Days', color='#440154', fontweight='bold')
ax2 = ax1.twinx()
ax2.plot(df_geo['customer_state'], df_geo['delay_rate_pct'], color='#fde725', marker='s', linewidth=2.5)
ax2.set_ylabel('Delay Rate (%)', color='#b5a100', fontweight='bold')
ax2.grid(False)
plt.title('Logistics Disparity: Delivery Days & Delay Rate Across Top States', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/06_geographic_logistics_disparity.png', dpi=150)
plt.close()
print("Saved Chart 6")

# Chart 7: Customer Spend Pareto
df_pareto = con.execute("""
    WITH customer_spends AS (
        SELECT c.customer_unique_id, ROUND(SUM(i.price + i.freight_value), 2) AS customer_spend
        FROM dim_customers c JOIN fact_orders o ON c.customer_id = o.customer_id JOIN fact_order_items i ON o.order_id = i.order_id
        WHERE o.order_status = 'delivered' GROUP BY c.customer_unique_id
    ),
    customer_deciles AS (
        SELECT customer_unique_id, customer_spend, NTILE(10) OVER (ORDER BY customer_spend DESC) AS spend_decile FROM customer_spends
    )
    SELECT spend_decile, ROUND(100.0 * SUM(customer_spend) / SUM(SUM(customer_spend)) OVER(), 2) AS decile_gmv_pct,
        ROUND(SUM(SUM(customer_spend)) OVER (ORDER BY spend_decile ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 / SUM(SUM(customer_spend)) OVER(), 2) AS cumulative_gmv_pct
    FROM customer_deciles GROUP BY spend_decile ORDER BY spend_decile
""").fetchdf()

plt.figure(figsize=(10, 5))
plt.plot([f'D{d}' for d in df_pareto['spend_decile']], df_pareto['cumulative_gmv_pct'], marker='o', color='#008080', linewidth=3)
plt.bar([f'D{d}' for d in df_pareto['spend_decile']], df_pareto['decile_gmv_pct'], color='#008080', alpha=0.35, width=0.5)
plt.axhline(80, color='crimson', linestyle='--')
plt.title('Customer Spend Pareto Decile Curve', fontsize=13, fontweight='bold')
plt.xlabel('Customer Deciles (D1=Top 10% to D10=Bottom 10%)', fontweight='bold')
plt.ylabel('Cumulative % of GMV', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/07_customer_pareto_concentration.png', dpi=150)
plt.close()
print("Saved Chart 7")

con.close()
print("Headless Chart Rendering Complete!")
