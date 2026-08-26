"""
generate_sales_data.py
Description: Generates realistic mock sales datasets in three different formats
(CSV for orders, JSON for products, and XLSX for customers)
to simulate a multi-source ETL pipeline.
"""

import os
import json
import random
import datetime
import pandas as pd

def generate_data():
    # Set seed for reproducibility
    random.seed(42)
    
    # Paths
    raw_dir = os.path.join("project_2_sales_etl", "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    products_path = os.path.join(raw_dir, "sales_products.json")
    customers_path = os.path.join(raw_dir, "sales_customers.xlsx")
    orders_path = os.path.join(raw_dir, "sales_orders.csv")
    
    print("Generating raw sales datasets...")

    # 1. GENERATE PRODUCTS (JSON format)
    # Define a clean catalog of products with different categories, list prices, and unit costs
    product_templates = [
        # Electronics
        ("Smartphones", "Alpha Phone 15", 999.00, 450.00),
        ("Smartphones", "Beta Phone Pro", 1199.00, 550.00),
        ("Laptops", "ZenBook Ultra 14", 1299.00, 680.00),
        ("Laptops", "Apex Book Pro 16", 1999.00, 1100.00),
        ("Accessories", "NoiseCancel Headphones", 299.00, 110.00),
        ("Accessories", "Smart Watch Gen 5", 349.00, 140.00),
        # Apparel
        ("Shoes", "FlexRun Sneakers", 120.00, 40.00),
        ("Shoes", "TrailTrack Hiking Boots", 160.00, 65.00),
        ("Clothing", "Comfort Fit Jeans", 80.00, 25.00),
        ("Clothing", "Active Dry T-Shirt", 35.00, 10.00),
        ("Clothing", "Windbreaker Jacket", 110.00, 42.00),
        # Furniture
        ("Chairs", "Ergo Comfort Chair", 399.00, 180.00),
        ("Chairs", "Mesh Task Chair", 199.00, 90.00),
        ("Desks", "Standing Office Desk", 599.00, 260.00),
        ("Desks", "Compact Writing Desk", 249.00, 110.00),
        ("Storage", "5-Shelf Bookcase", 149.00, 60.00),
        # Grocery / Lifestyle
        ("Beverages", "Premium Espresso Beans 1kg", 29.99, 12.00),
        ("Beverages", "Matcha Green Tea Powder", 24.99, 9.50),
        ("Kitchenware", "Stainless Steel Cookware Set", 199.99, 85.00),
        ("Kitchenware", "Digital Air Fryer 5L", 129.99, 52.00)
    ]
    
    products = []
    for i, (sub_cat, name, list_p, cost_p) in enumerate(product_templates):
        # Determine main category
        if sub_cat in ["Smartphones", "Laptops", "Accessories"]:
            category = "Electronics"
        elif sub_cat in ["Shoes", "Clothing"]:
            category = "Apparel"
        elif sub_cat in ["Chairs", "Desks", "Storage"]:
            category = "Furniture"
        else:
            category = "Lifestyle"
            
        products.append({
            "product_id": f"PROD{i+1:03d}",
            "product_name": name,
            "category": category,
            "sub_category": sub_cat,
            "list_price": list_p,
            "unit_cost": cost_p
        })
        
    # Write products to JSON
    with open(products_path, "w") as f:
        json.dump(products, f, indent=4)
    print(f"1. Generated {len(products)} products in {products_path}")

    # 2. GENERATE CUSTOMERS (Excel format)
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
                   "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    
    locations = [
        # (Country, State/Region, City)
        ("United States", "California", "Los Angeles"),
        ("United States", "California", "San Francisco"),
        ("United States", "New York", "New York"),
        ("United States", "Texas", "Houston"),
        ("United States", "Texas", "Austin"),
        ("United States", "Illinois", "Chicago"),
        ("Canada", "Ontario", "Toronto"),
        ("Canada", "British Columbia", "Vancouver"),
        ("United Kingdom", "England", "London"),
        ("United Kingdom", "England", "Manchester"),
        ("Germany", "Bavaria", "Munich"),
        ("Germany", "Berlin", "Berlin"),
        ("France", "Ile-de-France", "Paris"),
        ("France", "Provence", "Marseille")
    ]
    
    segments = ["Consumer", "Corporate", "Home Office"]
    
    customers = []
    num_customers = 500
    for i in range(num_customers):
        c_id = f"CUST{i+1:03d}"
        c_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        segment = random.choice(segments)
        country, state, city = random.choice(locations)
        
        customers.append({
            "customer_id": c_id,
            "customer_name": c_name,
            "segment": segment,
            "country": country,
            "state": state,
            "city": city
        })
        
    df_customers = pd.DataFrame(customers)
    df_customers.to_excel(customers_path, index=False, engine="openpyxl")
    print(f"2. Generated {num_customers} customers in {customers_path}")

    # 3. GENERATE ORDERS (CSV format)
    start_date = datetime.date(2024, 1, 1)
    end_date = datetime.date(2026, 6, 30)
    delta_days = (end_date - start_date).days
    
    channels = ["Online", "Mobile App", "Retail Store"]
    # Common discounts
    discounts = [0.0, 0.0, 0.0, 0.05, 0.1, 0.15, 0.2]
    
    orders = []
    num_orders = 8000
    
    for i in range(num_orders):
        order_id = f"ORD{i+1:05d}"
        
        # Pick customer & product
        cust = random.choice(customers)
        prod = random.choice(products)
        
        # Random date
        random_days = random.randint(0, delta_days)
        o_date = start_date + datetime.timedelta(days=random_days)
        
        # Random ship delay (1 to 6 days)
        ship_delay = random.randint(1, 6)
        s_date = o_date + datetime.timedelta(days=ship_delay)
        
        # Random qty (mostly 1-2, occasionally more)
        qty = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
        
        # Random discount (mostly none, occasionally some)
        discount = random.choice(discounts)
        
        # Sales Channel
        channel = random.choice(channels)
        
        orders.append({
            "order_id": order_id,
            "customer_id": cust["customer_id"],
            "product_id": prod["product_id"],
            "order_date": o_date.strftime("%Y-%m-%d"),
            "ship_date": s_date.strftime("%Y-%m-%d"),
            "quantity": qty,
            "discount": discount,
            "sales_channel": channel
        })
        
    df_orders = pd.DataFrame(orders)
    # Sort orders by date
    df_orders = df_orders.sort_values("order_date").reset_index(drop=True)
    # Re-apply sorted order IDs so they increase chronologically
    df_orders["order_id"] = [f"ORD{j+1:05d}" for j in range(num_orders)]
    
    df_orders.to_csv(orders_path, index=False)
    print(f"3. Generated {num_orders} orders in {orders_path}")
    print("Generation complete! Multi-source files are ready for ETL pipeline.")

if __name__ == "__main__":
    generate_data()
