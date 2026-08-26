"""
sales_etl.py
Description: Automated Extract, Transform, and Load (ETL) pipeline
for E-commerce/Retail Sales data. Consolidates CSV, JSON, and Excel formats
into an optimized Star Schema SQLite database, logging performance metadata.
"""

import os
import sys
import time
import json
import sqlite3
import datetime
import pandas as pd

def run_etl():
    start_time = time.time()
    
    # Paths
    db_path = os.path.join("project_2_sales_etl", "data", "sales_warehouse.db")
    schema_path = os.path.join("project_2_sales_etl", "sql", "sales_schema.sql")
    
    raw_dir = os.path.join("project_2_sales_etl", "data", "raw")
    orders_csv = os.path.join(raw_dir, "sales_orders.csv")
    products_json = os.path.join(raw_dir, "sales_products.json")
    customers_xlsx = os.path.join(raw_dir, "sales_customers.xlsx")
    
    # Initialize connection
    print(f"Connecting to SQLite Warehouse at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Deploy Schema DDL
    print(f"Deploying Star Schema structure from {schema_path}...")
    try:
        with open(schema_path, "r") as ddl_file:
            ddl_sql = ddl_file.read()
        cursor.executescript(ddl_sql)
        conn.commit()
        print("Schema tables initialized successfully.")
    except Exception as ddl_err:
        print(f"Failed to deploy schema: {ddl_err}")
        conn.close()
        return False
        
    extracted_files_count = 0
    records_loaded_count = 0
    status = "SUCCESS"
    error_msg = None

    try:
        # ==========================================
        # 1. EXTRACT PHASE
        # ==========================================
        print("\n--- [1/3] Extract Phase ---")
        
        # Verify existence of files
        for f_path in [orders_csv, products_json, customers_xlsx]:
            if not os.path.exists(f_path):
                raise FileNotFoundError(f"Missing source file: {f_path}")
                
        print(f"Extracting Orders CSV from: {orders_csv}")
        df_orders_raw = pd.read_csv(orders_csv)
        extracted_files_count += 1
        
        print(f"Extracting Products JSON from: {products_json}")
        with open(products_json, "r") as f:
            prod_data = json.load(f)
        df_products_raw = pd.DataFrame(prod_data)
        extracted_files_count += 1
        
        print(f"Extracting Customers Excel from: {customers_xlsx}")
        df_customers_raw = pd.read_excel(customers_xlsx, engine="openpyxl")
        extracted_files_count += 1
        
        print(f"Extraction Complete. Loaded {len(df_orders_raw)} orders, {len(df_products_raw)} products, and {len(df_customers_raw)} customers from disk.")

        # ==========================================
        # 2. TRANSFORM PHASE
        # ==========================================
        print("\n--- [2/3] Transform Phase ---")
        
        # 2.1 Transform Customers
        print("Transforming dim_customers...")
        # Check for missing customer IDs
        df_customers = df_customers_raw.dropna(subset=["customer_id"]).drop_duplicates(subset=["customer_id"])
        
        # 2.2 Transform Products
        print("Transforming dim_products...")
        # Verify columns and handle missing prices
        df_products = df_products_raw.dropna(subset=["product_id"]).drop_duplicates(subset=["product_id"])
        
        # 2.3 Transform Dates (Generate dim_date calendar table)
        print("Transforming dim_date calendar...")
        # Extract all unique date strings from order_date and ship_date
        all_dates = pd.concat([df_orders_raw["order_date"], df_orders_raw["ship_date"]]).dropna().unique()
        
        date_records = []
        for dt_str in all_dates:
            try:
                dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d").date()
                date_key = int(dt.strftime("%Y%m%d"))
                
                # Quarters range from 1 to 4
                quarter = (dt.month - 1) // 3 + 1
                
                date_records.append({
                    "date_key": date_key,
                    "full_date": dt_str,
                    "year": dt.year,
                    "quarter": quarter,
                    "month": dt.month,
                    "month_name": dt.strftime("%B"),
                    "day_of_week": dt.weekday(), # Monday = 0, Sunday = 6
                    "day_name": dt.strftime("%A"),
                    "is_weekend": 1 if dt.weekday() >= 5 else 0
                })
            except Exception as e:
                print(f"Error parsing date string '{dt_str}': {e}")
                
        df_date = pd.DataFrame(date_records).drop_duplicates(subset=["date_key"])
        
        # 2.4 Transform Sales Fact (fact_sales)
        print("Compiling fact_sales details...")
        # Clean basic orders first
        df_orders = df_orders_raw.dropna(subset=["order_id", "customer_id", "product_id"])
        
        # Join orders with products to retrieve unit prices and manufacturing costs
        df_sales_joined = df_orders.merge(df_products[["product_id", "list_price", "unit_cost"]], on="product_id", how="left")
        
        # Perform financial calculations
        df_sales_joined["gross_revenue"] = df_sales_joined["quantity"] * df_sales_joined["list_price"]
        df_sales_joined["discount_amount"] = df_sales_joined["gross_revenue"] * df_sales_joined["discount"]
        df_sales_joined["net_revenue"] = df_sales_joined["gross_revenue"] - df_sales_joined["discount_amount"]
        df_sales_joined["total_cost"] = df_sales_joined["quantity"] * df_sales_joined["unit_cost"]
        df_sales_joined["net_profit"] = df_sales_joined["net_revenue"] - df_sales_joined["total_cost"]
        df_sales_joined["margin_pct"] = (df_sales_joined["net_profit"] / df_sales_joined["net_revenue"]) * 100
        
        # Calculate shipping delay (in days)
        o_date_parsed = pd.to_datetime(df_sales_joined["order_date"])
        s_date_parsed = pd.to_datetime(df_sales_joined["ship_date"])
        df_sales_joined["shipping_delay_days"] = (s_date_parsed - o_date_parsed).dt.days
        
        # Generate foreign keys for dates (YYYYMMDD)
        df_sales_joined["order_date_key"] = o_date_parsed.dt.strftime("%Y%m%d").astype(int)
        df_sales_joined["ship_date_key"] = s_date_parsed.dt.strftime("%Y%m%d").astype(int)
        
        # Filter and structure facts columns
        fact_cols = [
            "order_id", "customer_id", "product_id", "order_date_key", "ship_date_key",
            "quantity", "discount", "gross_revenue", "discount_amount", "net_revenue",
            "total_cost", "net_profit", "margin_pct", "shipping_delay_days", "sales_channel"
        ]
        df_sales = df_sales_joined[fact_cols]
        records_loaded_count = len(df_sales)
        
        print("Transform Phase Complete. Calculations successfully validated.")

        # ==========================================
        # 3. LOAD PHASE
        # ==========================================
        print("\n--- [3/3] Load Phase ---")
        
        # Write to SQLite
        print("Loading dim_customers into database...")
        df_customers.to_sql("dim_customers", conn, if_exists="append", index=False)
        
        print("Loading dim_products into database...")
        df_products.to_sql("dim_products", conn, if_exists="append", index=False)
        
        print("Loading dim_date into database...")
        df_date.to_sql("dim_date", conn, if_exists="append", index=False)
        
        print("Loading fact_sales facts into database...")
        df_sales.to_sql("fact_sales", conn, if_exists="append", index=False)
        
        print("Load Phase Complete. Consolidated records committed to database.")

    except Exception as e:
        status = "FAILED"
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"\n❌ Pipeline failed during transform/load phases: {error_msg}")
        conn.rollback()
        
    finally:
        # Measure duration
        duration = time.time() - start_time
        print(f"\nETL Execution status: {status} in {duration:.3f} seconds.")
        
        # Log metadata to database
        try:
            cursor.execute("""
                INSERT INTO etl_log (status, extracted_files, records_loaded, execution_time_sec, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (status, extracted_files_count, records_loaded_count, duration, error_msg))
            conn.commit()
            print("ETL Run details logged successfully to metadata warehouse table 'etl_log'.")
        except Exception as log_err:
            print(f"Warning: Failed to write to etl_log metadata table: {log_err}")
            
        conn.close()
        print("Database connection closed.")
        
    return status == "SUCCESS"

if __name__ == "__main__":
    run_etl()
