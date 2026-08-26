-- sales_schema.sql
-- Star Schema DDL definitions for Sales Data Warehouse

-- Drop tables in order of dependencies (facts first, then dimensions)
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS etl_log;

-- 1. Customer Dimension
CREATE TABLE dim_customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT,
    country TEXT,
    state TEXT,
    city TEXT
);

-- 2. Product Dimension
CREATE TABLE dim_products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    list_price REAL,
    unit_cost REAL
);

-- 3. Date Dimension (Standard Data Warehousing Calendar table)
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY, -- Format: YYYYMMDD
    full_date TEXT NOT NULL,      -- Format: YYYY-MM-DD
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day_of_week INTEGER NOT NULL, -- 0 (Monday) to 6 (Sunday)
    day_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL   -- 0 (False) or 1 (True)
);

-- 4. Sales Fact Table
CREATE TABLE fact_sales (
    order_id TEXT NOT NULL,
    customer_id TEXT,
    product_id TEXT,
    order_date_key INTEGER,
    ship_date_key INTEGER,
    quantity INTEGER NOT NULL,
    discount REAL NOT NULL,
    gross_revenue REAL NOT NULL,      -- quantity * list_price
    discount_amount REAL NOT NULL,    -- gross_revenue * discount
    net_revenue REAL NOT NULL,        -- gross_revenue - discount_amount
    total_cost REAL NOT NULL,         -- quantity * unit_cost
    net_profit REAL NOT NULL,         -- net_revenue - total_cost
    margin_pct REAL NOT NULL,         -- (net_profit / net_revenue) * 100
    shipping_delay_days INTEGER,      -- ship_date - order_date
    sales_channel TEXT,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (ship_date_key) REFERENCES dim_date(date_key)
);

-- 5. ETL Pipeline Execution Log (Metadata table)
CREATE TABLE etl_log (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,             -- 'SUCCESS' or 'FAILED'
    extracted_files INTEGER,          -- Number of source files processed
    records_loaded INTEGER,           -- Row count inserted into fact_sales
    execution_time_sec REAL,          -- Execution duration in seconds
    error_message TEXT                -- Stack trace if FAILED
);
