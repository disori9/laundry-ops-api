import sqlite3
import random
from datetime import datetime, timedelta
import math
import csv

# Phase 1: Connect to the existing database you built
conn = sqlite3.connect('laundry.db')
cursor = conn.cursor()

print("Connected to database. Generating mock data...")

# Phase 2a: Generate 50 Mock Customers
# We use a simple loop to insert placeholder names and fake phone numbers.
for i in range(1, 51):
    fake_name = f"Customer_{i}"
    fake_number = f"555-01{random.randint(10,99)}"
    
    cursor.execute(
        "INSERT INTO customers (cust_name, number) VALUES (?, ?)", 
        (fake_name, fake_number)
    )

# We copy your exact FastAPI pricing logic over
def get_load_price(weight: float) -> int:
    if weight <= 0: return 0
    if weight <= 6.0: return 170
    elif weight <= 6.25: return 175
    elif weight <= 6.50: return 180
    elif weight <= 6.75: return 185
    elif weight <= 7.00: return 190
    elif weight <= 7.25: return 200  
    elif weight <= 7.50: return 205
    elif weight <= 7.75: return 210
    elif weight <= 8.00: return 220
    elif weight <= 8.25: return 225  
    else: return 235

print("Generating 30 days of orders and baskets...")

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
order_id_counter = 1

# Phase 2b: Generate the Orders
for day_offset in range(30):
    current_date = start_date + timedelta(days=day_offset)
    daily_orders = random.randint(15, 35) # Random volume per day
    
    for _ in range(daily_orders):
        # 1. Generate a random weight between a light load and a massive pile
        weight_kg = round(random.uniform(2.5, 22.0), 1)
        
        # 2. Your exact backend logic for loads and pricing
        clothes_loads = math.ceil(weight_kg / 8.5)
        weight_per_load = weight_kg / clothes_loads
        
        # We will randomly add a comforter (210 price) to 15% of orders to make data messy/realistic
        has_comforter = random.random() < 0.15 
        comforter_count = 1 if has_comforter else 0
        comforter_price = 210 * comforter_count
        
        total_loads = clothes_loads + comforter_count
        total_price = (get_load_price(weight_per_load) * clothes_loads) + comforter_price
        
        # 3. Randomize metadata
        status = random.choice(['PAID', 'PAID', 'PAID', 'UNPAID']) 
        cust_id = random.randint(1, 50)
        order_time = current_date.replace(
            hour=random.randint(8, 19), 
            minute=random.randint(0, 59)
        )
        
        # Insert the Order
        cursor.execute('''
            INSERT INTO orders (weight_kg, total_price, payment_status, customer_id, total_loads, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (weight_kg, total_price, status, cust_id, total_loads, order_time.strftime('%Y-%m-%d %H:%M:%S')))
        
        # Phase 2c: Generate the Baskets (order_loads)
        # For every load calculated above, we create a machine record
        for _ in range(total_loads):
            machine_no = random.randint(1, 6) # Assuming 6 machines
            cursor.execute('''
                INSERT INTO order_loads (order_id, status, machine_no)
                VALUES (?, 'COMPLETED', ?)
            ''', (order_id_counter, machine_no))
            
        order_id_counter += 1

conn.commit()
print(f"Successfully generated {order_id_counter - 1} highly realistic orders.")

# Phase 3: The Extraction
print("Extracting flat dataset for Looker Studio...")

# The SQL JOIN flattens the relational data for the BI tool
export_query = """
    SELECT 
        DATE(o.created_at) as order_date,
        o.order_id,
        o.weight_kg,
        o.total_price,
        ol.machine_no
    FROM orders o
    JOIN order_loads ol ON o.order_id = ol.order_id
"""
cursor.execute(export_query)
rows = cursor.fetchall()

# Write the flattened data to a CSV
with open('looker_dashboard_data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Order_Date', 'Order_ID', 'Weight_KG', 'Total_Price', 'Machine_No'])
    writer.writerows(rows)

conn.close()
print("Success! 'looker_dashboard_data.csv' is ready.")

