"""
Проверить товары в базе
"""
import sqlite3

conn = sqlite3.connect('shop.db')
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT id, subcategory, subcategory_type, quantity FROM products WHERE quantity > 0")

print("ТОВАРЫ В БАЗЕ:")
print("=" * 50)
for row in cursor.fetchall():
    print(f"ID: {row['id']}")
    print(f"  Subcategory: {row['subcategory']}")
    print(f"  Type: {row['subcategory_type']}")
    print(f"  Quantity: {row['quantity']}")
    print()

conn.close()
