import os
import random
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Please set SUPABASE_URL and SUPABASE_KEY in your .env file!")

# Create HTTP-based Supabase REST client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_mock_data():
    print("Generating synthetic e-commerce dataset...")
    random.seed(42)
    
    # 1. Customers
    countries = ['USA', 'Canada', 'UK', 'Germany', 'France']
    customers = [
        {
            "customer_id": f"CUST_{i:04d}",
            "customer_name": f"Customer_{i}",
            "email": f"user_{i}@example.com",
            "country": random.choice(countries)
        } for i in range(1, 201)
    ]

    # 2. Products
    products = [
        {"product_id": "PROD_001", "product_name": "Wireless Headphones", "category": "Electronics", "price": 99.99},
        {"product_id": "PROD_002", "product_name": "Smart Watch", "category": "Electronics", "price": 199.99},
        {"product_id": "PROD_003", "product_name": "Cotton T-Shirt", "category": "Clothing", "price": 24.99},
        {"product_id": "PROD_004", "product_name": "Denim Jeans", "category": "Clothing", "price": 59.99},
        {"product_id": "PROD_005", "product_name": "Coffee Maker", "category": "Home & Kitchen", "price": 79.99},
        {"product_id": "PROD_006", "product_name": "Python Programming Book", "category": "Books", "price": 39.99},
    ]

    # 3. Orders (60 Days of data)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    orders = []
    order_counter = 1
    
    current_date = start_date
    while current_date <= end_date:
        daily_order_count = random.randint(30, 50)
        
        is_revenue_drop_day = (current_date.date() == (end_date - timedelta(days=15)).date())
        is_refund_spike_day = (current_date.date() == (end_date - timedelta(days=7)).date())
        is_volume_spike_day = (current_date.date() == (end_date - timedelta(days=2)).date())

        if is_volume_spike_day:
            daily_order_count = random.randint(180, 220)

        for _ in range(daily_order_count):
            prod = random.choice(products)
            cust = random.choice(customers)
            qty = random.randint(1, 3)
            
            if is_revenue_drop_day:
                status = random.choices(['completed', 'cancelled'], weights=[0.2, 0.8])[0]
            elif is_refund_spike_day:
                status = random.choices(['completed', 'refunded'], weights=[0.5, 0.5])[0]
            else:
                status = random.choices(['completed', 'cancelled', 'refunded'], weights=[0.85, 0.10, 0.05])[0]

            orders.append({
                "order_id": f"ORD_{order_counter:06d}",
                "order_date": (current_date + timedelta(minutes=random.randint(0, 1430))).isoformat(),
                "customer_id": cust["customer_id"],
                "product_id": prod["product_id"],
                "quantity": qty,
                "unit_price": prod["price"],
                "total_amount": round(qty * prod["price"], 2),
                "status": status
            })
            order_counter += 1
            
        current_date += timedelta(days=1)

    return customers, products, orders

def batch_insert(table_name: str, data: list, batch_size: int = 200):
    print(f"Uploading {table_name} table ({len(data)} records)...")
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        supabase.table(table_name).upsert(batch).execute()

def load_to_supabase():
    customers, products, orders = generate_mock_data()
    
    print("Connecting to Supabase via HTTP REST API...")
    batch_insert('customers', customers)
    batch_insert('products', products)
    batch_insert('orders', orders, batch_size=300)
    
    print("✅ Seed dataset successfully loaded into Supabase PostgreSQL!")

if __name__ == "__main__":
    load_to_supabase()