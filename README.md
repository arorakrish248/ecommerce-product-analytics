# E-Commerce Product Analytics: Customer Retention, Unit Economics & Logistics Friction

A hands-on, end-to-end product analytics project investigating customer retention, fulfillment performance, and unit economics on a real-world e-commerce marketplace (100k+ orders, $15.4M GMV).

---

## 💡 The Business Problem

When looking at top-line numbers, the marketplace appeared to be thriving: **monthly order volume grew over 7x between early 2017 and mid-2018**, generating over **$15.4M in total GMV**.

However, digging under the surface revealed a classic **"leaky bucket"** problem:
* **97.0% of customers bought once and never returned** (overall repeat purchase rate was only **3.0%**).
* **Delivery delays severely hurt customer trust:** when orders missed their promised delivery date, customer satisfaction dropped from **4.29 / 5.0** down to **2.57 / 5.0**, and 1-star reviews surged by nearly **6x**.
* **Shipping across states took twice as long (15 days vs. 8 days intra-state)**, leading to a 10.2% delay rate in peripheral regions.

This project uses SQL and Python to diagnose the root causes of customer churn, quantify the impact of delivery delays on retention, and design concrete product recommendations to fix unit economics.

---

## 🔍 Key Findings at a Glance

| Metric | Number | Takeaway |
| :--- | :--- | :--- |
| **Total GMV** | **$15.42 Million** | Across 96,478 delivered orders ($160.20 average order value). |
| **Repeat Purchase Rate** | **3.0%** | Only 2,801 out of 93,358 delivered buyers returned for a 2nd order. |
| **Month-1 Retention** | **0.4% – 0.7%** | Almost all cohorts saw customer activity drop to near zero after Month 0. |
| **On-Time vs. Late CSAT** | **4.29 ➔ 2.57 / 5.0** | Late deliveries had a 54.1% negative review rate vs. 9.2% for on-time orders. |
| **Inter-State Transit** | **15.0 Days (vs. 7.9 Days)** | Cross-state orders took twice as long and had higher delay rates. |
| **Revenue Concentration** | **Top 10% = 38.4% GMV** | The top 20% of customers accounted for 53.2% of all platform spend. |
| **Payment Preferences** | **78.3% Credit Card** | Buyers used an average of 3.5 installments to afford higher ticket items. |

---

## 📊 Visual Highlights

Charts generated directly from the database and saved in `reports/charts/`:

### 1. Platform Growth vs. Cohort Retention Decay
| Monthly Orders & GMV Growth | Customer Cohort Retention Heatmap |
| :---: | :---: |
| <img src="reports/charts/01_monthly_growth_trajectory.png" width="440"/> | <img src="reports/charts/02_cohort_retention_heatmap.png" width="440"/> |

### 2. The Impact of Delivery Delays & Geographic Disparity
| Delivery Delay vs. Customer Rating Drop | Delivery Times & Delay Rates Across States |
| :---: | :---: |
| <img src="reports/charts/04_delay_vs_csat_degradation.png" width="440"/> | <img src="reports/charts/06_geographic_logistics_disparity.png" width="440"/> |

### 3. Customer Segments & Revenue Concentration
| RFM Customer Segment Revenue | Customer Spend Pareto Distribution |
| :---: | :---: |
| <img src="reports/charts/03_rfm_customer_segments.png" width="440"/> | <img src="reports/charts/07_customer_pareto_concentration.png" width="440"/> |

---


---

## 🛠️ Technologies & Tools Used

| Layer | Tool / Technology | Purpose in Project |
| :--- | :--- | :--- |
| **Relational Database** | **PostgreSQL (pgAdmin 4)** | Production Star Schema modeling, multi-table joins, constraints, and query execution. |
| **Local SQL Engine** | **DuckDB** | Fast, zero-setup local SQL analytical engine for running automated test suites in seconds. |
| **Data Processing** | **Python (Pandas, NumPy)** | Data cleaning, datetime parsing, feature engineering (transit lead times, delay flags). |
| **Data Visualization** | **Matplotlib & Seaborn** | Generating publication-quality cohort heatmaps, Pareto curves, and CSAT degradation charts. |
| **Statistical Analysis** | **SciPy (`scipy.stats`)** | Hypothesis testing (Welch’s two-sample t-test on delivery delays vs. CSAT ratings). |
| **Interactive Notebook** | **Jupyter Notebook** | Exploratory data analysis, diagnostic walkthroughs, and executive charting. |
| **Version Control** | **Git & GitHub** | Project management, commit history, and public portfolio documentation. |

## 🗄️ Database Architecture

The dataset is structured as a relational Star Schema (`sql/schema.sql`):

```
       ┌──────────────────┐               ┌──────────────────┐
       │  dim_customers   │               │   dim_sellers    │
       ├──────────────────┤               ├──────────────────┤
       │ customer_id (PK) │               │ seller_id (PK)   │
       │ customer_unique_id│              │ seller_city      │
       │ customer_state   │               │ seller_state     │
       └────────┬─────────┘               └────────┬─────────┘
                │ 1:N                              │ 1:N
                ▼                                  ▼
       ┌─────────────────────────────────────────────────────┐
       │                    fact_orders                      │
       ├─────────────────────────────────────────────────────┤
       │ order_id (PK)                                       │
       │ customer_id (FK -> dim_customers)                   │
       │ order_purchase_timestamp, order_delivered_date      │
       │ delivery_days, estimated_days, is_delayed           │
       └────────┬──────────────────────────┬─────────────────┘
                │ 1:N                      │ 1:N
                ▼                          ▼
       ┌──────────────────┐       ┌──────────────────┐
       │ fact_order_items │       │fact_order_reviews│
       ├──────────────────┤       ├──────────────────┤
       │ order_id (FK)    │       │ review_id (PK)   │
       │ product_id (FK)  │       │ order_id (FK)    │
       │ seller_id (FK)   │       │ review_score     │
       │ price, freight   │       │ review_message   │
       └────────┬─────────┘       └──────────────────┘
                │ N:1
                ▼
       ┌──────────────────┐
       │   dim_products   │
       ├──────────────────┤
       │ product_id (PK)  │
       │ category_english │
       │ weight, dims     │
       └──────────────────┘
```

---

## 💻 SQL Analysis Breakdown (27 Business Queries)

All queries are organized in `sql/` and testable via `tests/test_sql_suite.py`:

* **[Data Quality & Integrity (Q1–Q5)](sql/data_quality.sql):** Checked key consistency, orphan records (0 found), impossible timestamps, and price/freight distributions. Reconciled payment values against item totals (99.1% match).
* **[Growth & Exploratory Trends (Q6–Q10)](sql/exploratory_analysis.sql):** Monthly GMV, Month-over-Month growth rates using `LAG()`, 3-month rolling averages, and order volume heatmaps by day and hour.
* **[Customer Retention & Cohorts (Q11–Q16)](sql/customer_analysis.sql):** Repeat order frequency, 30/60/90/180-day repeat purchase windows using `LEAD()`, Month-0 to Month-6 retention cohort matrices, and 7-tier RFM customer segmentation.
* **[Product & Category Performance (Q17–Q21)](sql/product_analysis.sql):** Top 15 categories by revenue, year-over-year category growth, identifying popular products with low satisfaction ratings, and cross-category market basket pairs.
* **[Logistics & Customer Experience (Q22–Q27)](sql/business_analysis.sql):** Quantifying the drop in review scores for late deliveries, regional fulfillment differences across 27 states, intra-state vs. inter-state shipping friction, and seller dispatch reliability.

---

## 🎯 Product Recommendations & Next Steps

1. **Automated Proactive Delay Credits:**
   * *Problem:* When orders arrive late, customer satisfaction crashes and buyers rarely return.
   * *Solution:* Automatically send a notification and a small wallet credit (e.g. $5–$10) whenever an order is delayed by more than 48 hours, turning a bad experience into an incentive to return.
   * *Target Metric:* Increase the 60-day repeat rate among delayed buyers from 1.4% to 3.5%.

2. **First-Purchase Re-Engagement:**
   * *Problem:* Repeat purchases drop sharply after the first 30 days.
   * *Solution:* Trigger personalized replenishment offers within 14–21 days of delivery for consumable categories like health and beauty.
   * *Target Metric:* Lift 30-day second-order conversion by +2.5 percentage points.

3. **Regional Seller Onboarding:**
   * *Problem:* Inter-state shipments take 15 days on average because most sellers are located in the Southeast.
   * *Solution:* Onboard local sellers in northern and northeastern hubs to reduce transit times and lower freight costs.

---

## 📁 Repository Organization

```text
├── data/
│   └── processed/             # Cleaned CSV files ready for database import
├── notebooks/
│   └── product_analysis.ipynb # Jupyter notebook with full analysis and charts
├── reports/
│   ├── charts/                # Exported high-resolution charts
│   ├── executive_summary.md   # High-level summary for stakeholders
│   ├── product_analysis.md    # Detailed product analysis report
│   └── insights.md            # Top 15 findings with supporting data
├── sql/
│   ├── schema.sql             # Table definitions, constraints, and indexes
│   ├── STEP1_CREATE_TABLES.sql # One-click table creation script for pgAdmin
│   ├── STEP2_IMPORT_DATA.sql  # Fast CSV data loading script
│   ├── data_quality.sql       # Queries 1–5: Data audits
│   ├── exploratory_analysis.sql # Queries 6–10: Growth and payment trends
│   ├── customer_analysis.sql  # Queries 11–16: Cohorts, retention, and RFM
│   ├── product_analysis.sql   # Queries 17–21: Categories and product ratings
│   └── business_analysis.sql  # Queries 22–27: Logistics and delivery SLAs
├── src/
│   ├── data_ingestion.py      # Script to download raw dataset
│   ├── data_cleaning.py       # Data cleaning and feature engineering
│   ├── database_loader.py     # Local database builder
│   └── feature_engineering.py # Chart generation script
├── tests/
│   ├── test_sql_suite.py      # Automated test runner for all 27 queries
│   └── audit_metrics.py       # Verification script for calculated numbers
├── PGADMIN_GUIDE.md           # Step-by-step setup guide for pgAdmin 4
├── requirements.txt           # Python packages
└── README.md                  # Project overview
```

---

## ⚡ How to Run This Project

### 1. Clone and Install Dependencies
```bash
git clone https://github.com/arorakrish248/ecommerce-product-analytics.git
cd ecommerce-product-analytics

python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the SQL Test Suite
To execute and verify all 27 business queries locally in seconds:
```bash
python tests/test_sql_suite.py
```

### 3. Running in PostgreSQL / pgAdmin 4
Check [`PGADMIN_GUIDE.md`](PGADMIN_GUIDE.md) for simple instructions:
1. Run `sql/STEP1_CREATE_TABLES.sql` in the Query Tool.
2. Run `sql/STEP2_IMPORT_DATA.sql` to load the data from `C:/Users/Public/ecommerce_analytics_data/`.

---

## 💼 Resume Bullets

* **Product Analytics & Retention:** *Built an end-to-end PostgreSQL/Python analytics pipeline on 100K+ marketplace orders ($15.4M GMV), writing 27 complex SQL queries (CTEs, Window Functions, RFM, Cohorts) to uncover that 97.0% of buyers were one-time users.*
* **Customer Experience & Unit Economics:** *Identified a steep drop in customer satisfaction from 4.29 to 2.57 / 5.0 for late deliveries (6x surge in 1-star reviews), designing a proactive credit system projected to recover up to \$1.85M in churned GMV.*
* **Fulfillment & Strategy:** *Analyzed inter-state logistics friction (+7.1 days transit time for cross-state orders) and proposed regional seller onboarding to improve delivery times and repeat purchase rates.*
