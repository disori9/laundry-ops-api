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
            customer_id INTEGER,
            total_loads INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                ON DELETE SET NULL
        );
''')

cursor.execute('''
        CREATE TABLE order_loads (
               load_id INTEGER PRIMARY KEY AUTOINCREMENT,
               order_id INTEGER,
               status TEXT CHECK(status IN ('RECEIVED', 'WASHING', 'DRYING', 'FOLDING', 'BAGGED', 'COMPLETED')),
               machine_no INTEGER,
               FOREIGN KEY (order_id) REFERENCES orders (order_id)
                       ON DELETE CASCADE)
               ''')

cursor.execute('''
        CREATE TABLE item_categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        );
''')

cursor.execute('''
        CREATE TABLE order_items (
            items_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            initial_count INTEGER NOT NULL,
            verified_count INTEGER,
            order_id INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES item_categories (category_id)
        );
''')

conn.commit()

conn.close()

print("Database and table created successfully!")