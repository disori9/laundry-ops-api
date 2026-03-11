from fastapi import FastAPI
import sqlite3
from schemas import CustomerCreate

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}


@app.post("/customers")
def create_customer(customer: CustomerCreate):
    conn = sqlite3.connect('laundry.db')
    
    cursor = conn.cursor()

    command = 'INSERT INTO customers(cust_name, number) VALUES (?, ?)'
    data_to_insert = (customer.cust_name, customer.number)

    cursor.execute(command, data_to_insert)

    conn.commit()

    conn.close()

    return {"message": "Customer created successfully", "name": customer.cust_name, "number": customer.number}

