import os
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configure styling for portfolio-grade figures
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Helvetica', 'Arial', 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

charts_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/reports/charts'
os.makedirs(charts_dir, exist_ok=True)
db_path = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/processed/ecommerce_analytics.duckdb'
con = duckdb.connect(db_path)

print("Starting Advanced Python Analytical & Visualization Suite...")

# 1. Chart 1: Growth Engine & MoM Revenue Trajectory
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
color = '#1f77b4'
ax1.set_xlabel('Purchase Month', fontsize=12, fontweight='bold', labelpad=10)
ax1.set_ylabel('Delivered Orders', color=color, fontsize=12, fontweight='bold')
bars = ax1.bar(df_growth['order_purchase_month'], df_growth['orders'], color=color, alpha=0.7, width=0.6, label='Monthly Orders')
ax1.tick_params(axis='y', labelcolor=color)
ax1.tick_params(axis='x', rotation=45)

ax2 = ax1.twinx()
color = '#d62728'
ax2.set_ylabel('Gross Merchandise Value ($)', color=color, fontsize=12, fontweight='bold')
lines = ax2.plot(df_growth['order_purchase_month'], df_growth['gmv'], color=color, marker='o', linewidth=2.5, label='Monthly GMV')
ax2.tick_params(axis='y', labelcolor=color)

plt.title('Platform Hypergrowth Trajectory: Monthly Delivered Orders & GMV (2017-2018)', fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()
plt.savefig(f'{charts_dir}/01_monthly_growth_trajectory.png', dpi=300)
plt.close()
print("Saved Chart 1: 01_monthly_growth_trajectory.png")

# 2. Chart 2: Customer Cohort Retention Heatmap
df_cohort = con.execute("""
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
        SELECT cohort_month, COUNT(DISTINCT customer_unique_id) AS num_users FROM customer_first_cohort GROUP BY cohort_month
    ),
    retention_data AS (
        SELECT 
            f.cohort_month,
            (CAST(SUBSTRING(a.activity_month, 1, 4) AS INT) - CAST(SUBSTRING(f.cohort_month, 1, 4) AS INT)) * 12 +
            (CAST(SUBSTRING(a.activity_month, 6, 2) AS INT) - CAST(SUBSTRING(f.cohort_month, 6, 2) AS INT)) AS month_index,
            COUNT(DISTINCT a.customer_unique_id) AS active_users
        FROM customer_first_cohort f
        JOIN customer_activities a ON f.customer_unique_id = a.customer_unique_id
        GROUP BY f.cohort_month, month_index
    )
    SELECT 
        r.cohort_month,
        s.num_users,
        r.month_index,
        ROUND(100.0 * r.active_users / s.num_users, 2) AS retention_pct
    FROM retention_data r
    JOIN cohort_size s ON r.cohort_month = s.cohort_month
    WHERE r.cohort_month >= '2017-01' AND r.cohort_month <= '2018-03' AND r.month_index BETWEEN 0 AND 6
    ORDER BY r.cohort_month, r.month_index
""").fetchdf()

pivot_retention = df_cohort.pivot(index='cohort_month', columns='month_index', values='retention_pct')
plt.figure(figsize=(11, 7))
sns.heatmap(pivot_retention, annot=True, fmt='.2f', cmap='YlGnBu', cbar_kws={'label': 'Retention Rate (%)'}, vmin=0, vmax=1.5)
plt.title('Monthly Customer Cohort Retention Heatmap (Severe Retention Drop-off Post Month 0)', fontsize=13, fontweight='bold', pad=15)
plt.xlabel('Months Since First Acquisition (Cohort Index)', fontsize=11, fontweight='bold')
plt.ylabel('Cohort Acquisition Month', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/02_cohort_retention_heatmap.png', dpi=300)
plt.close()
print("Saved Chart 2: 02_cohort_retention_heatmap.png")

# 3. Chart 3: RFM Customer Segmentation Matrix
df_rfm = con.execute("""
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
            CASE 
                WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions / VIP'
                WHEN r_score >= 3 AND f_score >= 2 THEN 'Loyal Potential'
                WHEN r_score >= 4 AND f_score = 1 THEN 'Recent New Customers'
                WHEN r_score = 3 AND f_score = 1 THEN 'Promising / Developing'
                WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk / Need Attention'
                WHEN r_score <= 2 AND f_score = 2 THEN 'About to Churn'
                WHEN r_score = 1 AND f_score = 1 THEN 'Lost / Inactive'
                ELSE 'Standard Customers'
            END AS customer_segment,
            monetary
        FROM rfm_scores
    )
    SELECT 
        customer_segment,
        COUNT(*) AS total_customers,
        ROUND(SUM(monetary), 2) AS total_gmv
    FROM rfm_segmented
    GROUP BY customer_segment
    ORDER BY total_gmv DESC
""").fetchdf()

fig, ax = plt.subplots(figsize=(12, 6))
colors = ['#2ca02c', '#1f77b4', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#d62728']
bars = ax.barh(df_rfm['customer_segment'], df_rfm['total_gmv'] / 1e6, color=colors[:len(df_rfm)], alpha=0.85)
ax.set_xlabel('Total Gross Merchandise Value (Million $)', fontsize=12, fontweight='bold')
ax.set_title('Customer Segmentation GMV Contribution (RFM Framework)', fontsize=14, fontweight='bold', pad=15)
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, f'${width:.2f}M', ha='left', va='center', fontsize=10, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{charts_dir}/03_rfm_customer_segments.png', dpi=300)
plt.close()
print("Saved Chart 3: 03_rfm_customer_segments.png")

# 4. Chart 4: Delivery Delay vs CSAT Review Degradation Curve
df_delay_csat = con.execute("""
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
        ROUND(100.0 * SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS negative_pct,
        COUNT(*) AS order_vol
    FROM fact_orders o
    JOIN fact_order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
""").fetchdf()

# Sort brackets logically
bracket_order = ['Early >7d', 'Early 1-7d', 'On-Time', 'Delayed 1-3d', 'Delayed 4-7d', 'Delayed 8-14d', 'Delayed >14d']
df_delay_csat['bracket_rank'] = df_delay_csat['delivery_bracket'].apply(lambda x: bracket_order.index(x) if x in bracket_order else 99)
df_delay_csat = df_delay_csat.sort_values('bracket_rank')

fig, ax1 = plt.subplots(figsize=(11, 6))
ax1.plot(df_delay_csat['delivery_bracket'], df_delay_csat['avg_csat'], color='#2ca02c', marker='o', linewidth=3, markersize=8, label='Avg Review Score (1-5)')
ax1.set_ylabel('Average Customer Review Score', color='#2ca02c', fontsize=12, fontweight='bold')
ax1.set_ylim(1, 5)
ax1.tick_params(axis='x', rotation=30)

ax2 = ax1.twinx()
ax2.bar(df_delay_csat['delivery_bracket'], df_delay_csat['negative_pct'], color='#d62728', alpha=0.35, width=0.5, label='% Detractors (1-2 Stars)')
ax2.set_ylabel('% Negative Detractor Reviews (1-2 Stars)', color='#d62728', fontsize=12, fontweight='bold')
ax2.set_ylim(0, 100)

plt.title('The Experience Cliff: Customer Satisfaction vs Logistics Delivery Delay', fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()
plt.savefig(f'{charts_dir}/04_delay_vs_csat_degradation.png', dpi=300)
plt.close()
print("Saved Chart 4: 04_delay_vs_csat_degradation.png")

# 5. Chart 5: Top 10 Product Categories GMV vs Average CSAT Score
df_cat = con.execute("""
    SELECT 
        p.product_category_name_english AS category,
        ROUND(SUM(i.price + i.freight_value), 2) AS total_gmv,
        ROUND(AVG(r.review_score), 2) AS avg_csat
    FROM fact_order_items i
    JOIN dim_products p ON i.product_id = p.product_id
    JOIN fact_orders o ON i.order_id = o.order_id
    JOIN fact_order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY p.product_category_name_english
    ORDER BY total_gmv DESC
    LIMIT 12
""").fetchdf()

plt.figure(figsize=(12, 6))
scatter = plt.scatter(df_cat['total_gmv']/1e6, df_cat['avg_csat'], s=df_cat['total_gmv']/5000, color='#3b528b', alpha=0.75, edgecolors='black', linewidth=1.5)
for i, row in df_cat.iterrows():
    plt.annotate(row['category'], (row['total_gmv']/1e6 + 0.02, row['avg_csat'] + 0.01), fontsize=9, fontweight='bold')

plt.axhline(4.0, color='red', linestyle='--', alpha=0.7, label='Benchmark Quality Threshold (4.0 Stars)')
plt.title('Top Product Categories: Revenue Volume vs Customer Satisfaction', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Category GMV ($ Millions)', fontsize=12, fontweight='bold')
plt.ylabel('Average Customer Rating (1-5 Stars)', fontsize=12, fontweight='bold')
plt.legend(loc='lower right')
plt.tight_layout()
plt.savefig(f'{charts_dir}/05_category_revenue_vs_satisfaction.png', dpi=300)
plt.close()
print("Saved Chart 5: 05_category_revenue_vs_satisfaction.png")

# 6. Chart 6: Geographic Fulfillment Disparity (Delivery Days & Delay Rate by State)
df_geo = con.execute("""
    SELECT 
        c.customer_state,
        COUNT(DISTINCT o.order_id) AS orders,
        ROUND(AVG(o.delivery_days), 1) AS avg_delivery_days,
        ROUND(100.0 * SUM(o.is_delayed) / COUNT(o.order_id), 1) AS delay_rate_pct
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_state
    HAVING COUNT(DISTINCT o.order_id) >= 500
    ORDER BY avg_delivery_days ASC
""").fetchdf()

fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.bar(df_geo['customer_state'], df_geo['avg_delivery_days'], color='#440154', alpha=0.75, label='Avg Delivery Days')
ax1.set_ylabel('Average Delivery Time (Days)', color='#440154', fontsize=12, fontweight='bold')
ax1.set_xlabel('Customer State (Southeast Core vs Outer Territories)', fontsize=12, fontweight='bold')

ax2 = ax1.twinx()
ax2.plot(df_geo['customer_state'], df_geo['delay_rate_pct'], color='#fde725', marker='s', linewidth=2.5, markersize=7, label='% Delayed Orders')
ax2.set_ylabel('Order Delay Rate (%)', color='#b5a100', fontsize=12, fontweight='bold')
ax2.grid(False)

plt.title('Geographic Fulfillment Friction: Delivery Days & Delay Rate Across Major States', fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()
plt.savefig(f'{charts_dir}/06_geographic_logistics_disparity.png', dpi=300)
plt.close()
print("Saved Chart 6: 06_geographic_logistics_disparity.png")

# 7. Chart 7: Customer Spend Decile Concentration (Pareto Curve)
df_pareto = con.execute("""
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
        ROUND(100.0 * SUM(customer_spend) / SUM(SUM(customer_spend)) OVER(), 2) AS decile_gmv_pct,
        ROUND(SUM(SUM(customer_spend)) OVER (ORDER BY spend_decile ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 / SUM(SUM(customer_spend)) OVER(), 2) AS cumulative_gmv_pct
    FROM customer_deciles
    GROUP BY spend_decile
    ORDER BY spend_decile
""").fetchdf()

plt.figure(figsize=(10, 5.5))
plt.plot([f'Decile {d}' for d in df_pareto['spend_decile']], df_pareto['cumulative_gmv_pct'], marker='o', color='#008080', linewidth=3)
plt.bar([f'Decile {d}' for d in df_pareto['spend_decile']], df_pareto['decile_gmv_pct'], color='#008080', alpha=0.35, width=0.5)
plt.axhline(80, color='crimson', linestyle='--', label='80% Revenue Threshold')
plt.title('Customer Revenue Pareto Distribution (Decile Concentration)', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Customer Spend Deciles (Top 10% to Bottom 10%)', fontsize=11, fontweight='bold')
plt.ylabel('Cumulative % of Platform GMV', fontsize=11, fontweight='bold')
plt.legend(loc='lower right')
plt.tight_layout()
plt.savefig(f'{charts_dir}/07_customer_pareto_concentration.png', dpi=300)
plt.close()
print("Saved Chart 7: 07_customer_pareto_concentration.png")

con.close()
print("All 7 High-Impact Analytical Charts Rendered & Exported Successfully!")
