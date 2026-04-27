"""
main_local.py  —  Local dev server using SQLite (laundry.db)
Run with:  uvicorn main_local:app --reload
Keep this file OUT of your production deployment (Render uses main.py + PostgreSQL).
"""
import sqlite3
import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "laundry.db"   # <-- adjust path if needed


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    return conn


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "awake (local SQLite)"}


@app.get("/")
def root():
    return {"message": "Local dev server — SQLite mode"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_load_price(weight: float) -> int:
    if weight <= 0:    return 0
    if weight <= 6.0:  return 170
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


# ── Customers ─────────────────────────────────────────────────────────────────

@app.post("/customers")
def create_customer(customer: CustomerCreate):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO customers (cust_name, number) VALUES (?, ?)",
        (customer.cust_name, customer.number)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"message": "Customer created", "customer_id": new_id,
            "name": customer.cust_name, "number": customer.number}


@app.get("/customers")
def get_all_customers():
    conn = get_db()
    rows = conn.execute(
        "SELECT customer_id, cust_name, number FROM customers"
    ).fetchall()
    conn.close()
    return {"customers": [
        {"customer_id": r["customer_id"], "customer_name": r["cust_name"], "number": r["number"]}
        for r in rows
    ]}


@app.get("/customers/summary")
def get_customers_summary():
    conn = get_db()
    customers_raw = conn.execute(
        "SELECT customer_id, cust_name, number FROM customers ORDER BY cust_name ASC"
    ).fetchall()
    orders_raw = conn.execute(
        "SELECT order_id, customer_id, payment_status FROM orders ORDER BY order_id DESC"
    ).fetchall()
    conn.close()

    history_by_customer = {}
    for order in orders_raw:
        cid = order["customer_id"]
        history_by_customer.setdefault(cid, []).append({
            "id": order["order_id"], "status": order["payment_status"]
        })

    customers = []
    for c in customers_raw:
        cid = c["customer_id"]
        history = history_by_customer.get(cid, [])
        unpaid = sum(1 for o in history if o["status"] == "UNPAID")
        customers.append({
            "id": cid, "name": c["cust_name"], "phone": c["number"],
            "visits": len(history), "unpaidCount": unpaid, "history": history
        })
    return {"customers": customers}


# ── Orders ────────────────────────────────────────────────────────────────────

@app.post("/orders")
def create_order(order: OrderCreate):
    total_price = order.comforter_count * 210
    total_loads = order.comforter_count

    if order.weight_kg:
        clothes_loads = math.ceil(order.weight_kg / 8.5)
        weight_per_load = order.weight_kg / clothes_loads
        total_price += get_load_price(weight_per_load) * clothes_loads
        total_loads += clothes_loads

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO orders (weight_kg, total_price, payment_status, customer_id, total_loads) VALUES (?, ?, ?, ?, ?)",
        (order.weight_kg, total_price, order.payment_status, order.customer_id, total_loads)
    )
    new_order_id = cursor.lastrowid
    loads_data = [(new_order_id, "RECEIVED")] * total_loads
    conn.executemany("INSERT INTO order_loads (order_id, status) VALUES (?, ?)", loads_data)
    conn.commit()
    conn.close()
    return {"message": "Order created", "order_id": new_order_id,
            "total_price": total_price, "calculated_loads": total_loads}


@app.get("/orders")
def get_all_orders(payment_status: Optional[str] = None):
    conn = get_db()
    if payment_status:
        rows = conn.execute(
            "SELECT order_id, weight_kg, total_price, customer_id, total_loads, created_at FROM orders WHERE payment_status = ?",
            (payment_status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT order_id, weight_kg, total_price, customer_id, total_loads, created_at FROM orders"
        ).fetchall()
    conn.close()
    return {"orders": [
        {"order_id": r["order_id"], "weight_kg": r["weight_kg"], "total_price": r["total_price"],
         "customer_id": r["customer_id"], "total_loads": r["total_loads"], "created_at": r["created_at"]}
        for r in rows
    ]}


@app.get("/orders/{order_id}")
def get_order_ticket(order_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT order_id, weight_kg, total_price, payment_status, customer_id FROM orders WHERE order_id = ?",
        (order_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")

    ticket = {
        "order_id": row["order_id"], "weight_kg": row["weight_kg"],
        "total_price": row["total_price"], "payment_status": row["payment_status"],
        "customer_id": row["customer_id"]
    }

    loads = conn.execute(
        "SELECT load_id, status, machine_no FROM order_loads WHERE order_id = ?", (order_id,)
    ).fetchall()
    ticket["baskets"] = [{"load_id": l["load_id"], "status": l["status"], "machine_no": l["machine_no"]} for l in loads]

    items = conn.execute(
        "SELECT category_id, initial_count, verified_count FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()
    ticket["items"] = [
        {"category_id": i["category_id"], "count": i["initial_count"],
         "verified_count": i["verified_count"] or 0}
        for i in items
    ]
    conn.close()
    return ticket


@app.patch("/orders/{order_id}/payment")
def update_order_payment(order_id: int, payment_data: PaymentUpdate):
    conn = get_db()
    conn.execute("UPDATE orders SET payment_status = ? WHERE order_id = ?",
                 (payment_data.payment_status, order_id))
    conn.commit()
    conn.close()
    return {"message": "Payment updated"}


@app.patch("/orders/{order_id}/bag-all")
def bag_all_folding_loads(order_id: int):
    conn = get_db()
    cursor = conn.execute(
        "UPDATE order_loads SET status = 'BAGGED', machine_no = NULL WHERE order_id = ? AND status = 'FOLDING'",
        (order_id,)
    )
    conn.commit()
    conn.close()
    return {"message": f"Bagged {cursor.rowcount} load(s) for order {order_id}"}


@app.patch("/orders/{order_id}/complete-all")
def complete_all_bagged_loads(order_id: int, payment_data: Optional[PaymentUpdate] = None):
    conn = get_db()
    if payment_data and payment_data.payment_status:
        conn.execute("UPDATE orders SET payment_status = ? WHERE order_id = ?",
                     (payment_data.payment_status, order_id))
    cursor = conn.execute(
        "UPDATE order_loads SET status = 'COMPLETED', machine_no = NULL WHERE order_id = ? AND status = 'BAGGED'",
        (order_id,)
    )
    conn.commit()
    conn.close()
    return {"message": f"Completed {cursor.rowcount} load(s) for order {order_id}"}


# ── Loads ─────────────────────────────────────────────────────────────────────

@app.patch("/loads/{load_id}/status")
def update_load_status(load_id: int, status_update: LoadStatusUpdate):
    conn = get_db()
    if status_update.status in ("WASHING", "DRYING"):
        if status_update.machine_no is None:
            raise HTTPException(status_code=400, detail="Machine number required.")
        if status_update.machine_no not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="Invalid machine number.")
        count = conn.execute(
            "SELECT COUNT(load_id) FROM order_loads WHERE status = ? AND machine_no = ?",
            (status_update.status, status_update.machine_no)
        ).fetchone()[0]
        if count >= 1:
            raise HTTPException(status_code=400, detail="Machine in use.")
    conn.execute("UPDATE order_loads SET status = ?, machine_no = ? WHERE load_id = ?",
                 (status_update.status, status_update.machine_no, load_id))
    conn.commit()
    conn.close()
    return {"message": f"Load {load_id} updated to {status_update.status}"}


# ── Shop Floor ────────────────────────────────────────────────────────────────

@app.get("/shop-floor")
def get_shop_floor():
    conn = get_db()
    orders_raw = conn.execute('''
        SELECT DISTINCT o.order_id, o.weight_kg, o.total_price, o.payment_status,
               o.customer_id, o.total_loads, o.created_at, c.cust_name, c.number
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        JOIN order_loads ol ON o.order_id = ol.order_id
        WHERE ol.status != 'COMPLETED'
        ORDER BY o.order_id
    ''').fetchall()

    if not orders_raw:
        conn.close()
        return {"orders": []}

    order_ids = tuple(r["order_id"] for r in orders_raw)
    placeholders = ",".join("?" * len(order_ids))

    loads_raw = conn.execute(
        f"SELECT load_id, order_id, status, machine_no FROM order_loads WHERE order_id IN ({placeholders})",
        order_ids
    ).fetchall()
    items_raw = conn.execute(
        f"SELECT order_id, category_id, initial_count, verified_count FROM order_items WHERE order_id IN ({placeholders})",
        order_ids
    ).fetchall()
    conn.close()

    loads_by_order = {}
    for l in loads_raw:
        loads_by_order.setdefault(l["order_id"], []).append(
            {"load_id": l["load_id"], "status": l["status"], "machine_no": l["machine_no"]}
        )

    items_by_order = {}
    for i in items_raw:
        items_by_order.setdefault(i["order_id"], []).append(
            {"category_id": i["category_id"], "count": i["initial_count"],
             "verified_count": i["verified_count"] or 0}
        )

    orders = []
    for r in orders_raw:
        oid = r["order_id"]
        orders.append({
            "order_id": oid, "weight_kg": r["weight_kg"], "total_price": r["total_price"],
            "payment_status": r["payment_status"], "customer_id": r["customer_id"],
            "total_loads": r["total_loads"], "created_at": r["created_at"],
            "customer_name": r["cust_name"] or "Unknown",
            "customer_number": r["number"] or "N/A",
            "baskets": loads_by_order.get(oid, []),
            "items": items_by_order.get(oid, [])
        })
    return {"orders": orders}


# ── Order Items ───────────────────────────────────────────────────────────────

@app.post("/order-items")
def create_order_item(order_item: OrderItemCreate):
    conn = get_db()
    conn.execute(
        "INSERT INTO order_items (order_id, category_id, initial_count) VALUES (?, ?, ?)",
        (order_item.order_id, order_item.category_id, order_item.initial_count)
    )
    conn.commit()
    conn.close()
    return {"message": "Item added"}


@app.get("/orders/{order_id}/items")
def get_order_items(order_id: int):
    conn = get_db()
    rows = conn.execute('''
        SELECT ic.category_name, oi.initial_count, oi.verified_count
        FROM order_items oi
        JOIN item_categories ic ON oi.category_id = ic.category_id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    conn.close()
    return {"order_id": order_id, "items": [
        {"category": r["category_name"], "initial_count": r["initial_count"],
         "verified_count": r["verified_count"]}
        for r in rows
    ]}


@app.patch("/orders/{order_id}/items/{category_id}")
def verify_order_item(order_id: int, category_id: int, verification: ItemVerification):
    conn = get_db()
    cursor = conn.execute(
        "UPDATE order_items SET verified_count = ? WHERE order_id = ? AND category_id = ?",
        (verification.verified_count, order_id, category_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    conn.commit()
    conn.close()
    return {"message": f"Verified count updated"}