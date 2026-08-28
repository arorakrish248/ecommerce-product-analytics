import os
import duckdb

proc_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/processed'
db_path = os.path.join(proc_dir, 'ecommerce_analytics.duckdb')

if os.path.exists(db_path):
    os.remove(db_path)

con = duckdb.connect(db_path)
tables = [
    'dim_customers',
    'dim_products',
    'dim_sellers',
    'fact_orders',
    'fact_order_items',
    'fact_order_payments',
    'fact_order_reviews'
]

for tbl in tables:
    fpath = f"{proc_dir}/{tbl}.csv"
    con.execute(f"CREATE TABLE {tbl} AS SELECT * FROM read_csv_auto('{fpath}')")
    cnt = con.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
    print(f"Table {tbl}: {cnt:,} rows loaded.")

con.close()
print("DuckDB database created and verified successfully!")
