"""
Тестовый скрипт для проверки базы данных SQLite
"""

import sys
import os
from pathlib import Path

# Фикс кодировки для Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

sys.path.insert(0, str(Path(__file__).parent))

from database import (
    init_database,
    init_categories,
    add_or_update_user,
    get_user,
    set_admin_status,
    is_admin,
    add_product,
    get_product,
    get_all_products,
    update_product,
    create_order,
    add_order_item,
    get_order,
    add_review,
    get_product_reviews,
    get_db_connection
)
from analytics import get_full_statistics, format_statistics_report


def test_database():
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ SQLite")
    print("=" * 50)

    # 1. Инициализация
    print("\n1. Инициализация базы данных...")
    init_database()
    init_categories()
    print("[OK] База данных инициализирована")

    # 2. Тест пользователей
    print("\n2. Тест пользователей...")
    add_or_update_user(123456, "test_user", "Иван", "Иванов", "+79991234567")
    user = get_user(123456)
    print(f"   Пользователь: {user['first_name']} {user['last_name']}")
    print(f"   Username: @{user['username']}")

    # 3. Тест админов
    print("\n3. Тест админов...")
    set_admin_status(123456, True)
    print(f"   Пользователь 123456 админ: {is_admin(123456)}")

    # 4. Тест категорий
    print("\n4. Тест категорий...")
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM categories")
        count = cursor.fetchone()['count']
        print(f"   Категорий в базе: {count}")
    
    # 5. Тест товаров
    print("\n5. Тест товаров...")
    test_product = {
        'id': 'test_prod_001',
        'category_id': 1,
        'subcategory': 'Цыпленок бройлер',
        'subcategory_type': 'Охлажденное',
        'name': 'Цыпленок бройлер охлажденный',
        'price': 300,
        'price_per_kg': True,
        'average_weight': 2.5,
        'quantity': 10,
        'photo_id': None
    }
    add_product(test_product)
    product = get_product('test_prod_001')
    print(f"   Товар: {product['name']}")
    print(f"   Цена: {product['price']} руб./кг")
    print(f"   Остаток: {product['quantity']} кг")

    # 6. Тест заказов
    print("\n6. Тест заказов...")
    order_data = {
        'id': 'ORDER_TEST_001',
        'user_id': 123456,
        'total_amount': 750,
        'delivery_cost': 300,
        'delivery_method': 'delivery',
        'delivery_address': 'Тестовая ул., д. 1',
        'customer_name': 'Иван',
        'customer_phone': '+79991234567'
    }
    create_order(order_data)
    add_order_item(
        'ORDER_TEST_001',
        'test_prod_001',
        'Цыпленок бройлер',
        1,
        300,
        750,
        weight=2.5
    )
    order = get_order('ORDER_TEST_001')
    print(f"   Заказ: #{order['id']}")
    print(f"   Сумма: {order['total_amount']} руб.")
    print(f"   Статус: {order['status']}")
    
    # 7. Тест отзывов
    print("\n7. Тест отзывов...")
    add_review('test_prod_001', 123456, 5, "Отличный продукт!")
    reviews = get_product_reviews('test_prod_001')
    print(f"   Отзывов: {len(reviews)}")
    if reviews:
        print(f"   Текст: {reviews[0]['text']}")
        print(f"   Оценка: {reviews[0]['rating']}")

    # 8. Тест статистики
    print("\n8. Тест статистики...")
    stats = get_full_statistics(days=30)
    print(f"   Заказов за 30 дней: {stats.get('total_orders', 0)}")
    print(f"   Выручка: {stats.get('summary', {}).get('total_revenue', 0):.0f} руб.")
    
    # 9. Форматированный отчет
    print("\n9. Форматированный отчет:")
    print("-" * 50)
    report = format_statistics_report(stats)
    # Удаляем HTML теги и эмодзи для консоли
    import re
    clean_report = re.sub(r'<[^>]+>', '', report)
    clean_report = re.sub(r'[\U0001F300-\U0001F9FF]', '', clean_report)
    print(clean_report.encode('cp1251', errors='ignore').decode('cp1251'))
    print("-" * 50)
    
    # 10. Проверка всех таблиц
    print("\nСтруктура базы данных:")
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row['name'] for row in cursor.fetchall()]
        print(f"   Таблиц: {len(tables)}")
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"   • {table}: {count} записей")
    
    print("\n" + "=" * 50)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 50)


if __name__ == '__main__':
    test_database()
