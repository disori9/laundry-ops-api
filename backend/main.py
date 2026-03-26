import os
import psycopg2
import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your Vercel frontend to connect
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Safely grabs the database URL from Render's hidden environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    # Connects to Neon.tech Postgres
    return psycopg2.connect(DATABASE_URL)


@app.get("/health")
def health_check():
    return {"status": "awake"}


@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}


@app.post("/customers")
def create_customer(customer: CustomerCreate):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # PostgreSQL uses %s instead of ?
            command = 'INSERT INTO customers(cust_name, number) VALUES (%s, %s) RETURNING customer_id'
            data_to_insert = (customer.cust_name, customer.number)
            cursor.execute(command, data_to_insert)
            new_customer_id = cursor.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    return {"message": "Customer created successfully", "customer_id": new_customer_id, "name": customer.cust_name, "number": customer.number}


def get_load_price(weight: float) -> int:
    """Calculates the price for a SINGLE machine load."""
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


@app.post("/orders")
def create_order(order: OrderCreate):
    total_price = 0
    comforter_price = 210
    total_loads = order.comforter_count
    total_price = order.comforter_count * comforter_price

    if order.weight_kg:
        clothes_loads = math.ceil(order.weight_kg / 8.5)
        weight_per_load = order.weight_kg / clothes_loads
        total_price += get_load_price(weight_per_load) * clothes_loads
        total_loads += clothes_loads

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Postgres needs "RETURNING order_id" instead of using cursor.lastrowid
            command = 'INSERT INTO orders(weight_kg, total_price, payment_status, customer_id, total_loads) VALUES (%s, %s, %s, %s, %s) RETURNING order_id'
            data_to_insert = (order.weight_kg, total_price, order.payment_status, order.customer_id, total_loads)
            
            cursor.execute(command, data_to_insert)
            new_order_id = cursor.fetchone()[0]
            
            loads_data = []
            for n in range(total_loads):
                loads_data.append((new_order_id, 'RECEIVED'))
            
            command = 'INSERT INTO order_loads(order_id, status) VALUES (%s, %s)'
            cursor.executemany(command, loads_data)

        conn.commit()
    finally:
        conn.close()

    return {
        "message": "Order created successfully", 
        "order_id": new_order_id, 
        "total_price": total_price,
        "calculated_loads": total_loads
    }


@app.post("/order-items")
def create_order_item(order_item: OrderItemCreate):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            command = "INSERT INTO order_items (order_id, category_id, initial_count) VALUES (%s, %s, %s)"
            data_to_insert = (order_item.order_id, order_item.category_id, order_item.initial_count)
            cursor.execute(command, data_to_insert)
        conn.commit()
    finally:
        conn.close()

    return {"message": "Successful input of items"}


@app.get("/orders/{order_id}/items")
def get_order_items(order_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            command = '''SELECT item_categories.category_name, order_items.initial_count, order_items.verified_count
            FROM order_items
            JOIN item_categories ON order_items.category_id = item_categories.category_id
            WHERE order_items.order_id = %s'''

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
    finally:
        conn.close()


@app.patch("/orders/{order_id}/items/{category_id}")
def verify_order_item(order_id: int, category_id: int, verification: ItemVerification):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            command = 'UPDATE order_items SET verified_count = %s WHERE order_id = %s AND category_id = %s'
            data_to_insert = (verification.verified_count, order_id, category_id)

            cursor.execute(command, data_to_insert)

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Item not found for this order")
        conn.commit()
    finally:
        conn.close()

    return {"message": f"Order {order_id} category {category_id} verified count updated to {verification.verified_count}"}



@app.get("/shop-floor")
def get_shop_floor():
    """
    Single-request replacement for the N+2 pattern on the shop floor page.
    Returns all active orders bundled with customer, baskets, and items — 3 DB queries total.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT DISTINCT
                    o.order_id, o.weight_kg, o.total_price, o.payment_status,
                    o.customer_id, o.total_loads, o.created_at,
                    c.cust_name, c.number
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.customer_id
                JOIN order_loads ol ON o.order_id = ol.order_id
                WHERE ol.status != 'COMPLETED'
                ORDER BY o.order_id
            ''')
            orders_raw = cursor.fetchall()

            if not orders_raw:
                return {"orders": []}

            order_ids = tuple(row[0] for row in orders_raw)
            placeholders = ','.join(['%s'] * len(order_ids))

            cursor.execute(
                f'SELECT load_id, order_id, status, machine_no FROM order_loads WHERE order_id IN ({placeholders})',
                order_ids
            )
            loads_raw = cursor.fetchall()

            cursor.execute(
                f'SELECT order_id, category_id, initial_count, verified_count FROM order_items WHERE order_id IN ({placeholders})',
                order_ids
            )
            items_raw = cursor.fetchall()

        loads_by_order = {}
        for load in loads_raw:
            oid = load[1]
            loads_by_order.setdefault(oid, []).append({
                "load_id": load[0], "status": load[2], "machine_no": load[3]
            })

        items_by_order = {}
        for item in items_raw:
            oid = item[0]
            items_by_order.setdefault(oid, []).append({
                "category_id": item[1],
                "count": item[2],
                "verified_count": int(item[3]) if item[3] is not None else 0
            })

        orders = []
        for row in orders_raw:
            oid = row[0]
            orders.append({
                "order_id": oid,
                "weight_kg": row[1],
                "total_price": row[2],
                "payment_status": row[3],
                "customer_id": row[4],
                "total_loads": row[5],
                "created_at": row[6],
                "customer_name": row[7] or "Unknown",
                "customer_number": row[8] or "N/A",
                "baskets": loads_by_order.get(oid, []),
                "items": items_by_order.get(oid, [])
            })

        return {"orders": orders}
    finally:
        conn.close()


@app.get("/orders")
def get_all_orders(payment_status: Optional[str] = None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if payment_status:
                command = 'SELECT order_id, weight_kg, total_price, customer_id, total_loads, created_at FROM orders WHERE payment_status = %s'
                cursor.execute(command, (payment_status,))
            else:
                command = 'SELECT order_id, weight_kg, total_price, customer_id, total_loads, created_at FROM orders'
                cursor.execute(command)
            
            raw_orders = cursor.fetchall()
        
        formatted_orders = []
        for row in raw_orders:
            item_and_count = {
                "order_id": row[0], 
                "weight_kg": row[1], 
                "total_price": row[2],
                "customer_id": row[3],
                "total_loads": row[4],
                "created_at": row[5]
            }
            formatted_orders.append(item_and_count)
        
        return {"orders": formatted_orders}
    finally:
        conn.close()


@app.patch("/loads/{load_id}/status")
def update_load_status(load_id: int, status_update: LoadStatusUpdate):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if status_update.status == 'WASHING' or status_update.status == 'DRYING':
                if status_update.machine_no is None:
                    raise HTTPException(status_code=400, detail="Machine number required.")
                
                if status_update.machine_no not in [1, 2, 3]:
                    raise HTTPException(status_code=400, detail="Invalid machine number. Must be 1, 2, or 3.")
                
                command = 'SELECT count(load_id) FROM order_loads WHERE status = %s AND machine_no = %s'
                cursor.execute(command, (status_update.status, status_update.machine_no))
                result = cursor.fetchone()

                if result[0] >= 1:
                    raise HTTPException(status_code=400, detail="Machine in use.")

            command = 'UPDATE order_loads SET status = %s, machine_no = %s WHERE load_id = %s'
            data_to_insert = (status_update.status, status_update.machine_no, load_id)
            cursor.execute(command, data_to_insert)
        conn.commit()
    finally:
        conn.close()
    
    return {"message": f"Load status updated. ID: {load_id} to {status_update.status}"}


@app.get("/orders/{order_id}")
def get_order_ticket(order_id: int):
    order_ticket = {}
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            command = 'SELECT order_id, weight_kg, total_price, payment_status, customer_id FROM orders WHERE order_id = %s'
            cursor.execute(command, (order_id,))
            results = cursor.fetchone()

            cursor.execute('SELECT payment_status, total_price FROM orders WHERE order_id = %s', (order_id,))
            order_info = cursor.fetchone()

            if results:
                order_ticket["order_id"] = results[0]
                order_ticket["weight_kg"] = results[1]
                order_ticket["total_price"] = results[2]
                order_ticket["payment_status"] = results[3]
                order_ticket["customer_id"] = results[4]
                order_ticket["payment_status"] = order_info[0]
                order_ticket["total_price"] = order_info[1]
            else:
                raise HTTPException(status_code=404, detail="Order doesn't exist")
            
            command = 'SELECT load_id, status, machine_no FROM order_loads WHERE order_id = %s'
            cursor.execute(command, (order_id,))
            loads = cursor.fetchall()
            order_ticket["baskets"] = []
            
            for load in loads:
                load_detail = {}
                load_detail["load_id"] = load[0]
                load_detail["status"] = load[1]
                load_detail["machine_no"] = load[2]
                order_ticket["baskets"].append(load_detail)

            cursor.execute('SELECT category_id, initial_count, verified_count FROM order_items WHERE order_id = %s', (order_id,))
            items = cursor.fetchall()
            
            order_ticket["items"] = []
            for item in items:
                item_detail = {
                    "category_id": item[0],
                    "count": item[1],
                    "verified_count": int(item[2]) if item[2] is not None else 0
                }
                order_ticket["items"].append(item_detail)
                
        return order_ticket
    finally:
        conn.close()


@app.get("/customers")
def get_all_customers():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            command = 'SELECT customer_id, cust_name, number FROM customers'
            cursor.execute(command)
            customers = cursor.fetchall()

        formatted_customers = []
        for customer in customers:
            customer_data = {
                "customer_id": customer[0],
                "customer_name": customer[1],
                "number": customer[2]
            }
            formatted_customers.append(customer_data)
        
        return {"customers": formatted_customers}
    finally:
        conn.close()


@app.patch("/orders/{order_id}/payment")
def update_order_payment(order_id: int, payment_data: PaymentUpdate):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE orders SET payment_status = %s WHERE order_id = %s', 
                           (payment_data.payment_status, order_id))
        conn.commit()
    finally:
        conn.close()
    return {"message": "Payment updated"}

@app.patch("/orders/{order_id}/bag-all")
def bag_all_folding_loads(order_id: int):
    """
    Bags every FOLDING load for an order in a single DB round-trip.
    Replaces the frontend's sequential loop of N individual PATCH /loads/{id}/status calls.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE order_loads SET status = 'BAGGED', machine_no = NULL WHERE order_id = %s AND status = 'FOLDING'",
                (order_id,)
            )
            updated = cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    return {"message": f"Bagged {updated} load(s) for order {order_id}"}


@app.patch("/orders/{order_id}/complete-all")
def complete_all_bagged_loads(order_id: int, payment_data: Optional[PaymentUpdate] = None):
    """
    Marks every BAGGED load as COMPLETED and optionally updates payment — 1 or 2 DB queries.
    Replaces the frontend's GET ticket + sequential loop of N PATCH /loads/{id}/status calls.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if payment_data and payment_data.payment_status:
                cursor.execute(
                    'UPDATE orders SET payment_status = %s WHERE order_id = %s',
                    (payment_data.payment_status, order_id)
                )
            cursor.execute(
                "UPDATE order_loads SET status = 'COMPLETED', machine_no = NULL WHERE order_id = %s AND status = 'BAGGED'",
                (order_id,)
            )
            updated = cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    return {"message": f"Completed {updated} load(s) for order {order_id}"}