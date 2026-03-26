import sqlite3


with sqlite3.connect('laundry.db') as conn:
    cursor = conn.cursor()

    command = "INSERT INTO item_categories (category_name) VALUES (?)"

    data = [
    ('SHIRT',),
    ('PANTS',),
    ('HAT',),
    ('UNDERWEAR',),
    ('SOCKS',)
    ]

    cursor.executemany(command, data)

    conn.commit()