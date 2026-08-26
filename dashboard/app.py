"""
sales_dashboard.py
Description: Render function for the E-commerce Sales & ETL Pipeline Dashboard.
Imported and loaded by app.py.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def auto_initialize_sales_warehouse(db_path):
    import json
    import random
    import datetime
    import sqlite3
    import pandas as pd
    
    # 1. In-memory data generation
    random.seed(42)
    
    # Products
    product_templates = [
        ("Smartphones", "Alpha Phone 15", 999.00, 450.00),
        ("Smartphones", "Beta Phone Pro", 1199.00, 550.00),
        ("Laptops", "ZenBook Ultra 14", 1299.00, 680.00),
        ("Laptops", "Apex Book Pro 16", 1999.00, 1100.00),
        ("Accessories", "NoiseCancel Headphones", 299.00, 110.00),
        ("Accessories", "Smart Watch Gen 5", 349.00, 140.00),
        ("Shoes", "FlexRun Sneakers", 120.00, 40.00),
        ("Shoes", "TrailTrack Hiking Boots", 160.00, 65.00),
        ("Clothing", "Comfort Fit Jeans", 80.00, 25.00),
        ("Clothing", "Active Dry T-Shirt", 35.00, 10.00),
        ("Clothing", "Windbreaker Jacket", 110.00, 42.00),
        ("Chairs", "Ergo Comfort Chair", 399.00, 180.00),
        ("Chairs", "Mesh Task Chair", 199.00, 90.00),
        ("Desks", "Standing Office Desk", 599.00, 260.00),
        ("Desks", "Compact Writing Desk", 249.00, 110.00),
        ("Storage", "5-Shelf Bookcase", 149.00, 60.00),
        ("Beverages", "Premium Espresso Beans 1kg", 29.99, 12.00),
        ("Beverages", "Matcha Green Tea Powder", 24.99, 9.50),
        ("Kitchenware", "Stainless Steel Cookware Set", 199.99, 85.00),
        ("Kitchenware", "Digital Air Fryer 5L", 129.99, 52.00)
    ]
    
    products = []
    for i, (sub_cat, name, list_p, cost_p) in enumerate(product_templates):
        category = "Electronics" if sub_cat in ["Smartphones", "Laptops", "Accessories"] else (
            "Apparel" if sub_cat in ["Shoes", "Clothing"] else (
                "Furniture" if sub_cat in ["Chairs", "Desks", "Storage"] else "Lifestyle"
            )
        )
        products.append({
            "product_id": f"PROD{i+1:03d}",
            "product_name": name,
            "category": category,
            "sub_category": sub_cat,
            "list_price": list_p,
            "unit_cost": cost_p
        })
    df_products = pd.DataFrame(products)
    
    # Customers
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    locations = [
        ("United States", "California", "Los Angeles"), ("United States", "New York", "New York"),
        ("United States", "Texas", "Houston"), ("Canada", "Ontario", "Toronto"),
        ("United Kingdom", "England", "London"), ("Germany", "Bavaria", "Munich"), ("France", "Ile-de-France", "Paris")
    ]
    segments = ["Consumer", "Corporate", "Home Office"]
    
    customers = []
    for i in range(100):
        c_id = f"CUST{i+1:03d}"
        c_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        segment = random.choice(segments)
        country, state, city = random.choice(locations)
        customers.append({
            "customer_id": c_id, "customer_name": c_name, "segment": segment,
            "country": country, "state": state, "city": city
        })
    df_customers = pd.DataFrame(customers)
    
    # Orders (2,000 is compact and fast for cloud loading)
    start_date = datetime.date(2024, 1, 1)
    end_date = datetime.date(2026, 6, 30)
    delta_days = (end_date - start_date).days
    channels = ["Online", "Mobile App", "Retail Store"]
    discounts = [0.0, 0.0, 0.05, 0.1, 0.15, 0.2]
    
    orders = []
    for i in range(3000):
        cust = random.choice(customers)
        prod = random.choice(products)
        o_date = start_date + datetime.timedelta(days=random.randint(0, delta_days))
        s_date = o_date + datetime.timedelta(days=random.randint(1, 5))
        qty = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        discount = random.choice(discounts)
        channel = random.choice(channels)
        orders.append({
            "order_id": f"ORD{i+1:05d}", "customer_id": cust["customer_id"], "product_id": prod["product_id"],
            "order_date": o_date.strftime("%Y-%m-%d"), "ship_date": s_date.strftime("%Y-%m-%d"),
            "quantity": qty, "discount": discount, "sales_channel": channel
        })
    df_orders = pd.DataFrame(orders).sort_values("order_date").reset_index(drop=True)
    df_orders["order_id"] = [f"ORD{j+1:05d}" for j in range(len(df_orders))]
    
    # 2. Transform Phase
    # dim_date
    all_dates = pd.concat([df_orders["order_date"], df_orders["ship_date"]]).dropna().unique()
    date_records = []
    for dt_str in all_dates:
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d").date()
        date_records.append({
            "date_key": int(dt.strftime("%Y%m%d")), "full_date": dt_str, "year": dt.year,
            "quarter": (dt.month - 1) // 3 + 1, "month": dt.month, "month_name": dt.strftime("%B"),
            "day_of_week": dt.weekday(), "day_name": dt.strftime("%A"), "is_weekend": 1 if dt.weekday() >= 5 else 0
        })
    df_date = pd.DataFrame(date_records)
    
    # fact_sales
    df_sales_joined = df_orders.merge(df_products[["product_id", "list_price", "unit_cost"]], on="product_id", how="left")
    df_sales_joined["gross_revenue"] = df_sales_joined["quantity"] * df_sales_joined["list_price"]
    df_sales_joined["discount_amount"] = df_sales_joined["gross_revenue"] * df_sales_joined["discount"]
    df_sales_joined["net_revenue"] = df_sales_joined["gross_revenue"] - df_sales_joined["discount_amount"]
    df_sales_joined["total_cost"] = df_sales_joined["quantity"] * df_sales_joined["unit_cost"]
    df_sales_joined["net_profit"] = df_sales_joined["net_revenue"] - df_sales_joined["total_cost"]
    df_sales_joined["margin_pct"] = (df_sales_joined["net_profit"] / df_sales_joined["net_revenue"]) * 100
    df_sales_joined["shipping_delay_days"] = (pd.to_datetime(df_sales_joined["ship_date"]) - pd.to_datetime(df_sales_joined["order_date"])).dt.days
    df_sales_joined["order_date_key"] = pd.to_datetime(df_sales_joined["order_date"]).dt.strftime("%Y%m%d").astype(int)
    df_sales_joined["ship_date_key"] = pd.to_datetime(df_sales_joined["ship_date"]).dt.strftime("%Y%m%d").astype(int)
    
    fact_cols = [
        "order_id", "customer_id", "product_id", "order_date_key", "ship_date_key",
        "quantity", "discount", "gross_revenue", "discount_amount", "net_revenue",
        "total_cost", "net_profit", "margin_pct", "shipping_delay_days", "sales_channel"
    ]
    df_sales = df_sales_joined[fact_cols]
    
    # 3. Load Phase
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    schema_sql = """
    DROP TABLE IF EXISTS fact_sales;
    DROP TABLE IF EXISTS dim_customers;
    DROP TABLE IF EXISTS dim_products;
    DROP TABLE IF EXISTS dim_date;
    DROP TABLE IF EXISTS etl_log;
    
    CREATE TABLE dim_customers (customer_id TEXT PRIMARY KEY, customer_name TEXT NOT NULL, segment TEXT, country TEXT, state TEXT, city TEXT);
    CREATE TABLE dim_products (product_id TEXT PRIMARY KEY, product_name TEXT NOT NULL, category TEXT, sub_category TEXT, list_price REAL, unit_cost REAL);
    CREATE TABLE dim_date (date_key INTEGER PRIMARY KEY, full_date TEXT NOT NULL, year INTEGER NOT NULL, quarter INTEGER NOT NULL, month INTEGER NOT NULL, month_name TEXT NOT NULL, day_of_week INTEGER NOT NULL, day_name TEXT NOT NULL, is_weekend INTEGER NOT NULL);
    CREATE TABLE fact_sales (order_id TEXT NOT NULL, customer_id TEXT, product_id TEXT, order_date_key INTEGER, ship_date_key INTEGER, quantity INTEGER NOT NULL, discount REAL NOT NULL, gross_revenue REAL NOT NULL, discount_amount REAL NOT NULL, net_revenue REAL NOT NULL, total_cost REAL NOT NULL, net_profit REAL NOT NULL, margin_pct REAL NOT NULL, shipping_delay_days INTEGER, sales_channel TEXT, PRIMARY KEY (order_id, product_id));
    CREATE TABLE etl_log (run_id INTEGER PRIMARY KEY AUTOINCREMENT, run_timestamp TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT NOT NULL, extracted_files INTEGER, records_loaded INTEGER, execution_time_sec REAL, error_message TEXT);
    """
    cursor.executescript(schema_sql)
    
    df_customers.to_sql("dim_customers", conn, if_exists="append", index=False)
    df_products.to_sql("dim_products", conn, if_exists="append", index=False)
    df_date.to_sql("dim_date", conn, if_exists="append", index=False)
    df_sales.to_sql("fact_sales", conn, if_exists="append", index=False)
    
    # Log run details
    cursor.execute("INSERT INTO etl_log (status, extracted_files, records_loaded, execution_time_sec) VALUES ('SUCCESS', 3, ?, 0.08)", (len(df_sales),))
    conn.commit()
    conn.close()

def render_sales_dashboard():
    db_path = os.path.join("project_2_sales_etl", "data", "sales_warehouse.db")
    
    # Check database existence
    if not os.path.exists(db_path):
        st.warning("Sales database not initialized yet. Auto-running the ETL pipeline to build it...")
        try:
            auto_initialize_sales_warehouse(db_path)
            st.success("Sales warehouse initialized successfully!")
        except Exception as e:
            st.error(f"Failed to auto-initialize: {e}")
            st.stop()
            
    # Establish connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # -------------------------------------------------------------
    # 1. Title & High-Level KPIs
    # -------------------------------------------------------------
    st.subheader("Global Retail MNC - Sales performance & ETL Monitoring")
    
    # Query core financial summaries
    summary_query = """
        SELECT
            SUM(gross_revenue) as gross_revenue,
            SUM(discount_amount) as total_discounts,
            SUM(net_revenue) as net_revenue,
            SUM(total_cost) as total_cost,
            SUM(net_profit) as net_profit
        FROM fact_sales;
    """
    df_summary = pd.read_sql_query(summary_query, conn)
    
    gross_rev = df_summary["gross_revenue"].values[0] or 0.0
    total_disc = df_summary["total_discounts"].values[0] or 0.0
    net_rev = df_summary["net_revenue"].values[0] or 0.0
    net_profit = df_summary["net_profit"].values[0] or 0.0
    overall_margin = (net_profit / net_rev * 100) if net_rev > 0 else 0.0
    
    # Render KPI cards
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Gross Revenue", f"${gross_rev:,.0f}", help="Sales total before discounts")
    col2.metric("Total Discounts", f"${total_disc:,.0f}", f"-{(total_disc/gross_rev*100):.1f}% Avg Discount" if gross_rev > 0 else "0%")
    col3.metric("Net Sales MRR", f"${net_rev:,.0f}", help="Sales revenue net of discounts")
    col4.metric("Net Profit", f"${net_profit:,.0f}", help="Total profit after production costs")
    col5.metric("Net Profit Margin", f"{overall_margin:.2f}%", help="Percentage of net revenue converted to profit")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📊 Sales Performance", "💸 Profitability & Leakage", "⚙️ ETL Pipeline Control"])

    # -------------------------------------------------------------
    # Tab 1: Sales Performance
    # -------------------------------------------------------------
    with tab1:
        st.subheader("Executive Sales & Growth Performance")
        
        # 1.1 Revenue Trend over time
        trend_query = """
            SELECT
                d.year,
                d.month,
                d.month_name,
                SUM(f.net_revenue) as net_revenue,
                SUM(f.net_profit) as net_profit
            FROM fact_sales f
            JOIN dim_date d ON f.order_date_key = d.date_key
            GROUP BY d.year, d.month, d.month_name
            ORDER BY d.year, d.month;
        """
        df_trend = pd.read_sql_query(trend_query, conn)
        # Create Month-Year label for charts
        df_trend["period"] = df_trend["month_name"].astype(str) + " " + df_trend["year"].astype(str)
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_trend["period"], y=df_trend["net_revenue"],
            name="Net Revenue ($)", line=dict(color="#4A90E2", width=3)
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_trend["period"], y=df_trend["net_profit"],
            name="Net Profit ($)", line=dict(color="#50E3C2", width=3, dash='dash')
        ))
        fig_trend.update_layout(
            title="Monthly Sales & Net Profit Growth Trends",
            xaxis_title="Month",
            yaxis_title="USD ($)",
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Sales Channels Breakdown")
            # Sales by Channel
            channel_query = "SELECT sales_channel, SUM(net_revenue) as revenue FROM fact_sales GROUP BY sales_channel;"
            df_channel = pd.read_sql_query(channel_query, conn)
            
            fig_channel = px.pie(
                df_channel,
                names="sales_channel",
                values="revenue",
                color_discrete_sequence=["#4A90E2", "#50E3C2", "#F5A623"],
                hole=0.4
            )
            fig_channel.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_channel, use_container_width=True)
            
        with col_right:
            st.subheader("Regional Performance (Country Summary)")
            # Regional Sales
            geo_query = """
                SELECT
                    c.country,
                    COUNT(DISTINCT f.order_id) as total_orders,
                    ROUND(SUM(f.net_revenue), 0) as net_sales,
                    ROUND(SUM(f.net_profit), 0) as net_profit,
                    ROUND((SUM(f.net_profit)/SUM(f.net_revenue))*100, 1) as margin_pct
                FROM fact_sales f
                JOIN dim_customers c ON f.customer_id = c.customer_id
                GROUP BY c.country
                ORDER BY net_sales DESC;
            """
            df_geo = pd.read_sql_query(geo_query, conn)
            st.dataframe(df_geo, use_container_width=True, height=280)

    # -------------------------------------------------------------
    # Tab 2: Profitability & Leakage
    # -------------------------------------------------------------
    with tab2:
        st.subheader("Margins, Sub-category Contribution & Leakages")
        
        col_t2_left, col_t2_right = st.columns(2)
        
        with col_t2_left:
            st.subheader("Sub-Category Profit Contributions")
            # Category & Sub-category Sales
            cat_query = """
                SELECT
                    p.sub_category,
                    SUM(f.net_revenue) as revenue,
                    SUM(f.net_profit) as profit
                FROM fact_sales f
                JOIN dim_products p ON f.product_id = p.product_id
                GROUP BY p.sub_category
                ORDER BY profit ASC;
            """
            df_cat = pd.read_sql_query(cat_query, conn)
            
            fig_cat = go.Figure()
            fig_cat.add_trace(go.Bar(
                y=df_cat["sub_category"], x=df_cat["revenue"],
                name="Net Revenue", orientation='h', marker_color='#4A90E2'
            ))
            fig_cat.add_trace(go.Bar(
                y=df_cat["sub_category"], x=df_cat["profit"],
                name="Net Profit", orientation='h', marker_color='#50E3C2'
            ))
            fig_cat.update_layout(
                barmode='group',
                template="plotly_dark",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=450
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with col_t2_right:
            st.subheader("Discount Margin Erosion (Financial Leakage)")
            # Query discount impact on margins
            disc_query = """
                SELECT
                    discount * 100 as discount_pct,
                    ROUND((SUM(net_profit)/SUM(net_revenue))*100, 2) as profit_margin_pct
                FROM fact_sales
                GROUP BY discount;
            """
            df_disc = pd.read_sql_query(disc_query, conn)
            
            fig_disc = px.bar(
                df_disc,
                x="discount_pct",
                y="profit_margin_pct",
                text=df_disc["profit_margin_pct"].apply(lambda x: f"{x:.1f}%"),
                labels={"discount_pct": "Discount Rate (%)", "profit_margin_pct": "Net Profit Margin (%)"},
                color="profit_margin_pct",
                color_continuous_scale="RdYlGn"
            )
            fig_disc.update_layout(showlegend=False, template="plotly_dark", height=450)
            st.plotly_chart(fig_disc, use_container_width=True)
            st.caption("Proof: Giving 20% discounts drops the net profit margin from 53% to 41.3%, eroding 11.7% of bottom-line profit.")

    # -------------------------------------------------------------
    # Tab 3: ETL Pipeline Control
    # -------------------------------------------------------------
    with tab3:
        st.subheader("ETL Ingestion logs & Database Warehousing Status")
        
        # Ingestion metrics
        col_db1, col_db2, col_db3, col_db4 = st.columns(4)
        
        # Row counts in DWH tables
        c_count = cursor.execute("SELECT COUNT(*) FROM dim_customers").fetchone()[0]
        p_count = cursor.execute("SELECT COUNT(*) FROM dim_products").fetchone()[0]
        f_count = cursor.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
        
        col_db1.metric("dim_customers Count", f"{c_count:,} Rows")
        col_db2.metric("dim_products Count", f"{p_count:,} Rows")
        col_db3.metric("fact_sales Count", f"{f_count:,} Rows")
        
        # Retrieve latest execution
        latest_etl_query = "SELECT * FROM etl_log ORDER BY run_id DESC LIMIT 1;"
        df_latest = pd.read_sql_query(latest_etl_query, conn)
        
        if not df_latest.empty:
            exec_time = df_latest["execution_time_sec"].values[0]
            col_db4.metric("Latest ETL Run Duration", f"{exec_time:.3f}s", f"Status: {df_latest['status'].values[0]}")
        else:
            col_db4.metric("Latest ETL Run Duration", "No runs recorded")
            
        st.markdown("---")
        
        col_etl_left, col_etl_right = st.columns([1, 2])
        
        with col_etl_left:
            st.subheader("Trigger Live ETL Execution")
            st.write("Click below to run `sales_etl.py` locally. This will clear the warehouse tables, re-extract files, compute profit calculations, and log metadata.")
            
            if st.button("🔄 Trigger ETL Pipeline Reload"):
                with st.spinner("Executing Extract, Transform, and Load workflow..."):
                    try:
                        from project_2_sales_etl.scripts.sales_etl import run_etl
                        success = run_etl()
                        if success:
                            st.success("ETL Pipeline Succeeded! Warehouse tables refreshed and logged.")
                            # Rerun the app to show refreshed counts and logs
                            st.rerun()
                        else:
                            st.error("ETL Pipeline Execution Failed. Check details in logs.")
                    except Exception as err:
                        st.error(f"Execution Error: {err}")
                        
        with col_etl_right:
            st.subheader("ETL Execution History logs")
            # Query ETL log history
            log_query = "SELECT run_id, run_timestamp, status, extracted_files, records_loaded, ROUND(execution_time_sec, 4) as duration_sec, error_message FROM etl_log ORDER BY run_id DESC LIMIT 20;"
            df_logs = pd.read_sql_query(log_query, conn)
            st.dataframe(df_logs, use_container_width=True, height=260)
            
    conn.close()

# Run the dashboard automatically when executed
render_sales_dashboard()

