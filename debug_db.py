"""
Проверка товаров в базе и их названий
"""
import sqlite3
import json

conn = sqlite3.connect('shop.db')
conn.row_factory = sqlite3.Row

print("=" * 60)
print("ВСЕ ТОВАРЫ В БАЗЕ:")
print("=" * 60)

cursor = conn.execute("""
    SELECT id, subcategory, subcategory_type, category_id, quantity, price 
    FROM products 
    WHERE quantity > 0
""")

for row in cursor.fetchall():
    print(f"\nID: {row['id']}")
    print(f"  Category ID: {row['category_id']}")
    print(f"  Subcategory: '{row['subcategory']}'")
    print(f"  Type: '{row['subcategory_type']}'")
    print(f"  Quantity: {row['quantity']}")
    print(f"  Price: {row['price']}")

print("\n" + "=" * 60)
print("КАТЕГОРИИ:")
print("=" * 60)

cursor = conn.execute("SELECT * FROM categories")
for row in cursor.fetchall():
    print(f"\nID: {row['id']}")
    print(f"  Name: '{row['name']}'")
    print(f"  Config: {row['config'][:100]}...")

conn.close()
