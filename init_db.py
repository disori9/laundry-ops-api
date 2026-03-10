import sqlite3

conn = sqlite3.connect('laundry.db')

cursor = conn.cursor()

cursor.execute('''
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cust_name TEXT NOT NULL,
            number TEXT NOT NULL
        );
''')

cursor.execute('''
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            weight_kg REAL NOT NULL,
            total_price INT NOT NULL,
            payment_status TEXT CHECK(payment_status IN ('PAID', 'UNPAID')),
            status TEXT CHECK(status IN ('RECEIVED', 'WASHING', 'DRYING', 'FOLDING', 'BAGGED', 'COMPLETED')),
            customer_id INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                ON DELETE SET NULL
        );
''')

cursor.execute('''
        CREATE TABLE order_items (
            items_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            initial_count INTEGER NOT NULL,
            verified_count INTEGER,
            order_id INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
                ON DELETE CASCADE
        );
''')

conn.commit()

conn.close()

print("Database and table created successfully!")