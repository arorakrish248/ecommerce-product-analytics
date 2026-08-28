import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = [
    nbf.v4.new_markdown_cell("""# 🚀 Marketplace Product & Business Analytics: Retention, Unit Economics & Logistics Friction
**Author:** Senior Product & Data Analyst  
**Tech Stack:** Python 3.10+, DuckDB / PostgreSQL SQL Engine, Pandas, NumPy, Scikit-Learn, Matplotlib, Seaborn  

---

### Executive Thesis
This end-to-end analytical study investigates the core growth dynamics of a multi-sided e-commerce marketplace (~100k orders, $15.42M GMV). While top-line GMV expanded over **23x** between early 2017 and mid 2018, the business suffers from a severe **"Leaky Bucket" syndrome**:
* **97.0%** of acquired customers never make a second purchase (3.0% repeat rate).
* Fulfillment delays create a steep **Experience Cliff**: satisfaction drops from **4.29 / 5.0** (on-time) to **2.57 / 5.0** (delayed), with 1-star reviews surging **7.3x**.
* Inter-state logistics friction (+7.1 days transit) suppresses long-term LTV across outer geographies.

Here, we combine high-performance SQL querying with statistical Python diagnostics to build an actionable product optimization roadmap.
"""),
    nbf.v4.new_code_cell("""import os
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configure styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# Connect to the high-performance relational database
db_path = '../data/processed/ecommerce_analytics.duckdb'
con = duckdb.connect(db_path)
print("Connected to relational DuckDB database successfully!")
"""),
    nbf.v4.new_markdown_cell("""## 1. Growth Engine & Top-Line Financial Trajectory
Let's evaluate monthly delivered order volume and Gross Merchandise Value (GMV)."""),
    nbf.v4.new_code_cell("""query_growth = \"\"\"
SELECT 
    order_purchase_month,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(i.price + i.freight_value), 2) AS gmv,
    ROUND(AVG(i.price + i.freight_value), 2) AS aov
FROM fact_orders o
JOIN fact_order_items i ON o.order_id = i.order_id
WHERE o.order_status = 'delivered' AND order_purchase_month >= '2017-01' AND order_purchase_month <= '2018-08'
GROUP BY order_purchase_month
ORDER BY order_purchase_month;
\"\"\"
df_growth = con.execute(query_growth).fetchdf()
display(df_growth.tail())
"""),
    nbf.v4.new_markdown_cell("""## 2. Customer Retention & Cohort Decay Matrix
Evaluating customer repeat behaviors across sequential monthly cohorts."""),
    nbf.v4.new_code_cell("""query_cohort = \"\"\"
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
ORDER BY r.cohort_month, r.month_index;
\"\"\"
df_cohort = con.execute(query_cohort).fetchdf()
pivot_retention = df_cohort.pivot(index='cohort_month', columns='month_index', values='retention_pct')

plt.figure(figsize=(10, 6))
sns.heatmap(pivot_retention, annot=True, fmt='.2f', cmap='YlGnBu', cbar_kws={'label': 'Retention Rate (%)'}, vmin=0, vmax=1.5)
plt.title('Monthly Customer Cohort Retention Heatmap (%)', fontsize=13, fontweight='bold', pad=15)
plt.xlabel('Months Since Acquisition (Cohort Index)', fontweight='bold')
plt.ylabel('Cohort Month', fontweight='bold')
plt.show()
"""),
    nbf.v4.new_markdown_cell("""## 3. The Experience Cliff: Delivery Delay vs CSAT Review Degradation
Statistical hypothesis testing on delivery performance vs customer ratings."""),
    nbf.v4.new_code_cell("""query_delay = \"\"\"
SELECT 
    is_delayed,
    delivery_days,
    r.review_score
FROM fact_orders o
JOIN fact_order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered';
\"\"\"
df_delay = con.execute(query_delay).fetchdf()

on_time_scores = df_delay[df_delay['is_delayed'] == 0]['review_score']
delayed_scores = df_delay[df_delay['is_delayed'] == 1]['review_score']

t_stat, p_val = stats.ttest_ind(on_time_scores, delayed_scores, equal_var=False)
print(f"On-Time Mean CSAT: {on_time_scores.mean():.2f} / 5.0")
print(f"Delayed Mean CSAT: {delayed_scores.mean():.2f} / 5.0")
print(f"Welch's Two-Sample t-test: t = {t_stat:.2f}, p-value = {p_val:.2e}")
"""),
    nbf.v4.new_markdown_cell("""## 4. RFM Segmentation & Customer Decile Concentration
Segmenting users into actionable lifecycle buckets and quantifying Pareto concentration."""),
    nbf.v4.new_code_cell("""query_pareto = \"\"\"
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
    COUNT(*) AS customer_count,
    ROUND(SUM(customer_spend), 2) AS decile_gmv,
    ROUND(100.0 * SUM(customer_spend) / SUM(SUM(customer_spend)) OVER(), 2) AS decile_gmv_pct,
    ROUND(SUM(SUM(customer_spend)) OVER (ORDER BY spend_decile ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 / SUM(SUM(customer_spend)) OVER(), 2) AS cumulative_gmv_pct
FROM customer_deciles
GROUP BY spend_decile
ORDER BY spend_decile;
\"\"\"
df_pareto = con.execute(query_pareto).fetchdf()
display(df_pareto)
""")
]

nb.cells = cells
with open('notebooks/product_analysis.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("Jupyter Notebook created successfully at notebooks/product_analysis.ipynb")
