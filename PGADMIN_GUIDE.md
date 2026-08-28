# 🐘 Complete Guide: Running the Analytics Suite in pgAdmin & Cloud PostgreSQL

You can run this entire project in **pgAdmin 4** (or any online cloud PostgreSQL service like Neon, Supabase, Aiven, or ElephantSQL) using the pre-built SQL scripts.

---

## Method 1: Running in pgAdmin 4 (Local)

### Step 1: Open pgAdmin & Create the Database
1. Open **pgAdmin 4** on your machine.
2. In the left sidebar (*Servers $\to$ PostgreSQL 18*), right-click on **Databases** $\to$ **Create** $\to$ **Database...**.
3. Name it: `ecommerce_analytics` and click **Save**.

### Step 2: Create Tables & Schema
1. Right-click on your new `ecommerce_analytics` database and select **Query Tool**.
2. Open or copy-paste the contents of [`sql/pgadmin_master_setup.sql`](file:///C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql/pgadmin_master_setup.sql).
3. Click the **Execute / Run (F5)** button.
4. All 7 dimension and fact tables, primary keys, foreign keys, and indexes will be created instantly.

### Step 3: Load the Processed Data (2 Options)

#### Option A: Using pgAdmin GUI Import (Easiest)
1. In pgAdmin, expand `ecommerce_analytics` $\to$ `Schemas` $\to$ `public` $\to$ `Tables`.
2. Right-click any table (e.g. `dim_customers`) $\to$ **Import/Export Data...**.
3. Set toggle to **Import**, select the corresponding CSV file from `data/processed/` (e.g. `dim_customers.csv`), enable **Header**, select delimiter `,`, and click **OK**.
4. Repeat for the 7 tables in this order (to satisfy Foreign Keys):
   1. `dim_customers`
   2. `dim_products`
   3. `dim_sellers`
   4. `fact_orders`
   5. `fact_order_items`
   6. `fact_order_payments`
   7. `fact_order_reviews`

#### Option B: Using SQL `COPY` Command
Run the commented `COPY` commands at the bottom of [`sql/pgadmin_master_setup.sql`](file:///C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql/pgadmin_master_setup.sql) pointing to your local `data/processed/*.csv` paths.

### Step 4: Run the 27 Business & Product SQL Analyses
Open the **Query Tool** in pgAdmin and open any of the 5 analysis files:
* [`sql/data_quality.sql`](file:///C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql/data_quality.sql) (Queries 1–5)
* [`sql/exploratory_analysis.sql`](file:///C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql/exploratory_analysis.sql) (Queries 6–10)
* [`sql/customer_analysis.sql`](file:///C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql/customer_analysis.sql) (Queries 11–16)
* [`sql/product_analysis.sql`](file:///C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql/product_analysis.sql) (Queries 17–21)
* [`sql/business_analysis.sql`](file:///C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql/business_analysis.sql) (Queries 22–27)

---

## Method 2: Free Online / Cloud PostgreSQL (Zero Setup)

If you prefer an online cloud database where you don't have to manage local server passwords:
1. Create a free PostgreSQL instance on **[Neon.tech](https://neon.tech)** or **[Supabase](https://supabase.com)** (takes ~30 seconds).
2. Open their built-in **SQL Editor**.
3. Run [`sql/pgadmin_master_setup.sql`](file:///C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql/pgadmin_master_setup.sql) to create the schema.
4. Upload the CSVs in `data/processed/` or connect via standard connection string (`postgres://...`).

---

## Method 3: Instant Local SQL Engine (Included & Ready to Go)

For immediate, zero-friction local execution without configuring database servers, the project is also fully pre-loaded into DuckDB:
```bash
python tests/test_sql_suite.py
```
This executes all 27 enterprise SQL queries against the complete dataset in ~2 seconds.
