from fastapi import FastAPI
import sqlite3
import math
from schemas import CustomerCreate, OrderCreate

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

        conn.commit()

    return {"message": f"Order created successfully, total price: {total_price}"}
