# 🚀 Multi-Sided E-Commerce Marketplace Product & Business Analytics Platform
**An End-to-End Product Analytics Study on Customer Retention, Unit Economics & Logistics Friction**

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)
![PostgreSQL / DuckDB](https://img.shields.io/badge/SQL-PostgreSQL%20%7C%20DuckDB-orange.svg)

---

## 📌 Executive Overview
This repository contains an end-to-end, portfolio-grade **Product & Business Analytics Project** simulating the strategic work of a Senior Product Analyst at a multi-category technology marketplace. 

Operating on a real-world relational dataset of **99,441 orders**, **96,096 unique customers**, and **$15.42M in Gross Merchandise Value (GMV)**, this project investigates why platform hypergrowth (+754% order volume expansion between 2017–2018) is bottlenecked by severe customer churn, logistics delivery friction, and low repeat purchase rates.

---

## 🏗️ Repository Architecture

```
ecommerce-product-analytics/
├── data/
│   ├── raw/                  # 8 Raw relational source CSVs (~100k records)
│   └── processed/            # Cleaned dimension & fact tables + DuckDB SQL engine
├── notebooks/
│   └── product_analysis.ipynb # Interactive Jupyter diagnostic notebook
├── src/
│   ├── data_ingestion.py      # Automated dataset ingestion pipeline
│   ├── data_cleaning.py       # Cleansing & feature engineering engine
│   ├── database_loader.py     # Relational database schema builder & data loader
│   ├── feature_engineering.py # Statistical aggregations & portfolio chart exporter
│   └── generate_charts.py     # High-resolution visualization generator
├── sql/
│   ├── schema.sql             # Enterprise PostgreSQL star/snowflake DDL & indexes
│   ├── data_quality.sql       # Queries 1–5: Reconciliation & referential integrity audits
│   ├── exploratory_analysis.sql # Queries 6–10: Growth, MoM trends, payment mixes & heatmaps
│   ├── customer_analysis.sql  # Queries 11–16: Cohorts, retention, RFM & Pareto deciles
│   ├── product_analysis.sql   # Queries 17–21: Category economics, product ratings & affinity
│   └── business_analysis.sql  # Queries 22–27: Logistics friction, delivery SLAs & CSAT
├── reports/
│   ├── charts/                # 7 High-resolution decision-useful analytical figures
│   ├── executive_summary.md   # High-level strategic report for Product Managers & Executives
│   ├── product_analysis.md    # Comprehensive product diagnostic & experiment roadmap
│   └── insights.md            # Top 15 critical business findings with evidentiary support
├── tests/
│   ├── test_sql_suite.py      # Automated SQL test suite executing all 27 business queries
│   └── audit_metrics.py       # Verification script ensuring zero data fabrication
├── .env.example               # Configuration template for PostgreSQL & local SQL engines
├── .gitignore                 # Exclusion rules for secrets, virtual environments & large files
├── requirements.txt           # Python dependency specifications
└── README.md                  # Master documentation & portfolio overview
```

---

## 📊 Relational Star Schema Model

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

## 🔑 Key Verified Business Findings & Real Metrics

1. **The "Leaky Bucket" Retention Crisis:** 
   * Out of **93,358 delivered customer profiles**, **97.0% (90,557)** never make a second purchase.
   * Month-1 cohort retention is strictly **0.4%–0.7%**, indicating growth is heavily reliant on top-of-funnel paid acquisition.
2. **The Logistics Experience Cliff:** 
   * On-time deliveries achieve an average review score of **4.29 / 5.0** (9.2% detractor rate).
   * Delayed deliveries trigger a catastrophic drop to **2.57 / 5.0** (54.1% detractor rate; Welch $t = 118.4, p < 0.0001$).
3. **Inter-State Fulfillment Penalty:** 
   * Cross-state shipments require **15.0 days on average** (vs. 7.9 days intra-state) and suffer a **10.2% delay rate**, creating a massive friction point for national expansion.
4. **Revenue Concentration:** 
   * Top 10% of customers generate **38.4% of platform GMV**; Top 20% generate **53.2% of GMV**.

---

## 🚀 Quickstart & Reproduction Guide

### 1. Clone & Setup Environment
```bash
git clone https://github.com/your-username/ecommerce-product-analytics.git
cd ecommerce-product-analytics
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Data Processing & Relational Loader
```bash
python src/data_ingestion.py
python src/data_cleaning.py
python src/database_loader.py
```

### 3. Run Automated SQL Test Suite (27 Queries)
```bash
python tests/test_sql_suite.py
```

### 4. Generate High-Impact Portfolio Charts
```bash
python src/feature_engineering.py
```

---

## 🎯 Defensible Resume Bullets
* **Product Analytics & Growth:** Architected a full-scale PostgreSQL/DuckDB analytics warehouse on 100K+ transactional orders ($15.4M GMV), performing 27 complex SQL analyses (CTEs, Window Functions, RFM, Cohorts) revealing that 97.0% of buyers are one-and-done churn risks.
* **Diagnostic Analytics & Strategy:** Uncovered a non-linear "Logistics Experience Cliff" showing delivery delays drop customer ratings from 4.29 to 2.57 / 5.0 and surge 1-star reviews by 5.8x (Welch $t=118.4, p<0.001$), proposing proactive automated recovery credits projected to reclaim \$1.85M in churned GMV.
* **Cross-Functional Impact & Experimentation:** Designed an A/B testing and dynamic SLA framework targeting cross-state logistics friction (+7.1 days transit penalty), establishing North Star retention metrics for product and operations roadmaps.
