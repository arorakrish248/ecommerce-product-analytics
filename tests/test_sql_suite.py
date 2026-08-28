import os
import duckdb
import pandas as pd

sql_dir = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/sql'
db_path = 'C:/Users/krish/.gemini/antigravity/scratch/ecommerce-product-analytics/data/processed/ecommerce_analytics.duckdb'

con = duckdb.connect(db_path)
sql_files = ['data_quality.sql', 'exploratory_analysis.sql', 'customer_analysis.sql', 'product_analysis.sql', 'business_analysis.sql']

total_queries_run = 0
for f in sql_files:
    fpath = os.path.join(sql_dir, f)
    with open(fpath, 'r', encoding='utf-8') as sql_file:
        content = sql_file.read()
    
    # Split queries by semicolon
    statements = [s.strip() for s in content.split(';') if s.strip() and not s.strip().startswith('-- =')]
    print(f"\n--- Testing {f} ({len(statements)} queries) ---")
    for idx, stmt in enumerate(statements, 1):
        if not stmt: continue
        try:
            res = con.execute(stmt).fetchdf()
            total_queries_run += 1
            print(f"  Query {idx}: SUCCESS ({len(res)} rows returned)")
        except Exception as e:
            print(f"  Query {idx} FAILED: {e}\n  Statement snippet: {stmt[:100]}...")

con.close()
print(f"\nTotal SQL Analyses Verified Successfully: {total_queries_run}/27")
