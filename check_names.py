"""
Проверка названий товаров в базе
Запустить на Bothost в консоли
"""
import sqlite3

conn = sqlite3.connect('shop.db')
cursor = conn.execute("SELECT subcategory, quantity FROM products")

print("ТОВАРЫ В БАЗЕ:")
print("=" * 50)
for row in cursor.fetchall():
    print(f"'{row[0]}' - {row[1]} шт.")

conn.close()
