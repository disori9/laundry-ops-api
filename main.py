from fastapi import FastAPI, HTTPException
from schemas import *
from typing import Optional
import sqlite3
import math


app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}


@app.post("/customers")
def create_customer(customer: CustomerCreate):
    with sqlite3.connect('laundry.db') as conn:
    
        cursor = conn.cursor()

        command = 'INSERT INTO customers(cust_name, number) VALUES (?, ?)'
        data_to_insert = (customer.cust_name, customer.number)

        cursor.execute(command, data_to_insert)

        conn.commit()

    return {"message": "Customer created successfully", "name": customer.cust_name, "number": customer.number}


def get_load_price(weight: float) -> int:
    """Calculates the price for a SINGLE machine load."""
    if weight <= 0: return 0
    if weight <= 6.0: return 170
    elif weight <= 6.25: return 175
    elif weight <= 6.50: return 180
    elif weight <= 6.75: return 185
    elif weight <= 7.00: return 190
    elif weight <= 7.25: return 200  # Irregular jump
    elif weight <= 7.50: return 205
    elif weight <= 7.75: return 210
    elif weight <= 8.00: return 220
    elif weight <= 8.25: return 225  # Irregular jump
    else: return 235                 # Covers up to the 8.5kg max limit


@app.post("/orders")
def create_order(order: OrderCreate):
    total_price = 0
    comforter_price = 210
    total_loads = order.comforter_count
    total_price = order.comforter_count * comforter_price

    # Basically, because an order is halved if it reaches above 8.5kg, we use math.ceil to get the total loads in an order
    # We need to have an if else section because a customer might bring only comforters
    if order.weight_kg:
        clothes_loads = math.ceil(order.weight_kg / 8.5)
        weight_per_load = order.weight_kg / clothes_loads
        total_price += get_load_price(weight_per_load) * clothes_loads
        total_loads += clothes_loads

    # --- DATABASE INSERT ---
    with sqlite3.connect('laundry.db') as conn:
        cursor = conn.cursor()
        
        command = 'INSERT INTO orders(weight_kg, total_price, payment_status, customer_id, total_loads) VALUES (?, ?, ?, ?, ?)'
        data_to_insert = (order.weight_kg, total_price, order.payment_status, order.customer_id, total_loads)
        
        cursor.execute(command, data_to_insert)
        new_order_id = cursor.lastrowid
        
        loads_data = []
        for n in range(total_loads):
            loads_data.append((new_order_id, 'RECEIVED'))
        
        command = 'INSERT INTO order_loads(order_id, status) VALUES (?, ?)'
        cursor.executemany(command, loads_data)

        conn.commit()

    return {
        "message": "Order created successfully", 
        "order_id": new_order_id, 
        "total_price": total_price,
        "calculated_loads": total_loads
    }


@app.post("/order-items")
def create_order_item(order_item: OrderItemCreate):
    with sqlite3.connect('laundry.db') as conn:
        cursor = conn.cursor()

        command = "INSERT INTO order_items (order_id, category_id, initial_count) VALUES (?, ?, ?)"

        data_to_insert = (order_item.order_id, order_item.category_id, order_item.initial_count)

        cursor.execute(command, data_to_insert)

        new_items_id = cursor.lastrowid

        conn.commit()

    return {"message": f"Successful input of items", "items_id": new_items_id}


@app.get("/orders/{order_id}/items")
def get_order_items(order_id: int):
    with sqlite3.connect('laundry.db') as conn:
        cursor = conn.cursor()

        command = '''SELECT item_categories.category_name, order_items.initial_count, order_items.verified_count
        FROM order_items
        JOIN item_categories ON order_items.category_id = item_categories.category_id
        WHERE order_items.order_id = ?'''

        cursor.execute(command, (order_id,))

        raw_items = cursor.fetchall()

        
    formatted_items = []
    for row in raw_items:
        item_and_count = {
            "category": row[0], 
            "initial_count": row[1], 
            "verified_count": row[2]
        }
        formatted_items.append(item_and_count)

    return {"order_id": order_id, "items": formatted_items}


@app.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, status_update: OrderStatusUpdate):
    with sqlite3.connect('laundry.db') as conn:
        cursor = conn.cursor()

        fetch_active_washing = 'SELECT SUM(total_loads) FROM orders WHERE status = ?'
        cursor.execute(fetch_active_washing, ('WASHING',))
        result = cursor.fetchone()
        current_loads = result or 0

        if current_loads < 3:
            command = 'UPDATE orders SET status = ? WHERE order_id = ?'

            data_to_insert = (status_update.status, order_id)

            cursor.execute(command, data_to_insert)

            conn.commit()
    
    return {"message": f"Successful change of status to {status_update.status}", "status": status_update.status}


@app.patch("/orders/{order_id}/items/{category_id}")
def verify_order_item(order_id: int, category_id: int, verification: ItemVerification):
    with sqlite3.connect('laundry.db') as conn:
        cursor = conn.cursor()

        command = 'UPDATE order_items SET verified_count = ? WHERE order_id = ? AND category_id = ?'

        data_to_insert = (verification.verified_count, order_id, category_id)

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found for this order")
    
        cursor.execute(command, data_to_insert)

        conn.commit()

    return {"message": f"Order {order_id} category {category_id} verified count updated to {verification.verified_count}"}


@app.get("/orders")
def get_all_orders(status: Optional[str] = None):
    with sqlite3.connect('laundry.db') as conn:
        cursor = conn.cursor()

        if status:
            command = 'SELECT order_id, weight_kg, total_price, payment_status, status FROM orders WHERE status = ?'
            
            cursor.execute(command, (status,))

        else:
            command = 'SELECT order_id, weight_kg, total_price, payment_status, status FROM orders'

            cursor.execute(command)
        
        raw_orders = cursor.fetchall()
    
    formatted_orders = []
    for row in raw_orders:
        item_and_count = {
            "order_id": row[0], 
            "weight_kg": row[1], 
            "total_price": row[2],
            "payment_status": row[3],
            "status": row[4]
        }
        formatted_orders.append(item_and_count)
    
    return {"orders": formatted_orders}


