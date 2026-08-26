"""
run_sales_queries.py
Description: Reads the analytical queries from sql/sales_queries.sql,
executes them against the SQLite sales warehouse, and prints the formatted results.
"""

import os
import sqlite3
import pandas as pd

def run_analysis():
    db_path = os.path.join("project_2_sales_etl", "data", "sales_warehouse.db")
    sql_path = os.path.join("project_2_sales_etl", "sql", "sales_queries.sql")
    
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} does not exist. Run sales_etl.py first.")
        return
    
    if not os.path.exists(sql_path):
        print(f"Error: SQL file {sql_path} does not exist.")
        return
        
    print(f"Connecting to database {db_path}...")
    conn = sqlite3.connect(db_path)
    
    print(f"Reading queries from {sql_path}...\n")
    with open(sql_path, "r") as f:
        sql_content = f.read()
        
    # Split the SQL content by queries
    raw_queries = sql_content.split(";")
    
    query_sections = [
        "1. CATEGORY PERFORMANCE",
        "2. MONTH-OVER-MONTH SALES REVENUE TREND",
        "3. DISCOUNT VS. MARGIN IMPACT ANALYSIS",
        "4. CUSTOMER SEGMENT & GEOGRAPHY PERFORMANCE",
        "5. ETL HEALTH CHECK LOGS"
    ]
    
    idx = 0
    for raw_q in raw_queries:
        query_str = raw_q.strip()
        if not query_str or query_str.startswith("/*") or len(query_str) < 10:
            continue
            
        section_name = query_sections[idx] if idx < len(query_sections) else f"Query {idx+1}"
        print(f"### {section_name}")
        print("-" * 50)
        
        try:
            # Run the query using pandas
            df = pd.read_sql_query(query_str, conn)
            # Print the dataframe as Markdown
            print(df.to_markdown(index=False))
            print("\n")
        except Exception as e:
            print(f"Error executing query: {e}")
            print(f"Query was:\n{query_str}\n")
            
        idx += 1
        
    conn.close()

if __name__ == "__main__":
    run_analysis()
