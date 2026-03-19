from fastapi import FastAPI
import sqlite3
import math
from schemas import *

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


@app.post("/orders")
def create_order(order: OrderCreate):
    kg_per_order = 6
    load = math.ceil(order.weight_kg / kg_per_order)
    total_price = 165 * load

    with sqlite3.connect('laundry.db') as conn:
        cursor = conn.cursor()

        command = 'INSERT INTO orders(weight_kg, total_price, payment_status, status, customer_id) VALUES (?, ?, ?, ?, ?)'
        data_to_insert = (order.weight_kg, total_price, order.payment_status, 'RECEIVED', order.customer_id)

        cursor.execute(command, data_to_insert)

        new_order_id = cursor.lastrowid

        conn.commit()

    return {"message": f"Order created successfully, total price: {total_price}", "order_id": new_order_id, "total_price": total_price}


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

        command = '''SELECT item_categories.category_name, order_items.initial_count
        FROM order_items
        JOIN item_categories ON order_items.category_id = item_categories.category_id
        WHERE order_items.order_id = ?'''

        cursor.execute(command, (order_id,))

        raw_items = cursor.fetchall()

        
    formatted_items = []
    for row in raw_items:
        item_and_count = {"category": row[0], "count": row[1]}
        formatted_items.append(item_and_count)

    return {"order_id": order_id, "items": formatted_items}



@app.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, status_update: OrderStatusUpdate):
    with sqlite3.connect('laundry.db') as conn:
        cursor = conn.cursor()

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

        cursor.execute(command, data_to_insert)

        conn.commit()

    return {"message": f"Order {order_id} category {category_id} verified count updated to {verification.verified_count}"}