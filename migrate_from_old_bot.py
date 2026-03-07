"""
Скрипт миграции данных из СТАРОГО бота в НОВЫЙ с SQLite
Сохраняет: товары, заказы, клиентов, корзины, подписки, статистику
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Добавляем путь к базе данных
sys.path.insert(0, str(Path(__file__).parent))

from database import (
    init_database,
    add_or_update_user,
    set_admin_status,
    add_product,
    create_order,
    add_order_item,
    get_db_connection
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== НАСТРОЙКИ ====================
# Путь к СТАРОМУ файлу с данными (из старого бота)
OLD_DATA_FILE = 'shop_data.json'  # Или укажите путь к файлу старого бота

# Путь к НОВОЙ базе данных (создается автоматически)
NEW_DB_FILE = 'shop.db'
# ==================================================


def load_old_data(filepath):
    """Загрузка данных из старого JSON файла"""
    if not os.path.exists(filepath):
        logger.error(f"❌ Файл {filepath} не найден!")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"✅ Загружены данные из {filepath}")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return None


def migrate_users(old_data):
    """Миграция пользователей (клиентов и админов)"""
    logger.info("\n👥 Миграция пользователей...")
    
    users_migrated = 0
    admins_migrated = 0
    
    # Получаем админов из старого бота
    admins = old_data.get('admins', [])
    
    # Мигрируем админов
    for admin_id in admins:
        try:
            set_admin_status(int(admin_id), True)
            admins_migrated += 1
            logger.info(f"  ✅ Админ: {admin_id}")
        except Exception as e:
            logger.warning(f"  ⚠️ Не удалось добавить админа {admin_id}: {e}")
    
    # Мигрируем пользователей из заказов
    orders = old_data.get('orders', {})
    user_ids = set()
    
    for order in orders.values():
        user_id = order.get('user_id')
        if user_id and user_id not in user_ids:
            user_ids.add(user_id)
            try:
                add_or_update_user(
                    user_id=int(user_id),
                    username=order.get('username', ''),
                    first_name=order.get('customer_name', ''),
                    phone=order.get('customer_phone', '')
                )
                users_migrated += 1
                logger.info(f"  ✅ Клиент: {user_id} ({order.get('customer_name', '')})")
            except Exception as e:
                logger.warning(f"  ⚠️ Не удалось добавить клиента {user_id}: {e}")
    
    # Мигрируем пользователей из уведомлений
    notifications = old_data.get('notifications', {})
    for product_id, user_list in notifications.items():
        for user_id in user_list:
            if user_id not in user_ids:
                user_ids.add(user_id)
                try:
                    add_or_update_user(int(user_id))
                    users_migrated += 1
                except Exception as e:
                    pass
    
    logger.info(f"✅ Мигрировано пользователей: {users_migrated}, админов: {admins_migrated}")
    return users_migrated, admins_migrated


def migrate_products(old_data):
    """Миграция товаров"""
    logger.info("\n🍗 Миграция товаров...")
    
    products = old_data.get('products', {})
    products_migrated = 0
    
    for product_id, product in products.items():
        try:
            # Определяем category_id
            category_name = product.get('category', '')
            category_id = get_category_id_by_name(category_name)
            
            if not category_id:
                logger.warning(f"  ⚠️ Не найдена категория для товара {product_id}: {category_name}")
                continue
            
            # Создаем товар
            product_data = {
                'id': product_id,
                'category_id': category_id,
                'subcategory': product.get('subcategory', ''),
                'subcategory_type': product.get('subcategory_type', ''),
                'name': product.get('name', product.get('subcategory', '')),
                'price': int(product.get('price', 0)),
                'price_per_kg': product.get('price_per_kg', False),
                'average_weight': product.get('average_weight'),
                'quantity': int(product.get('quantity', 0)),
                'photo_id': product.get('photo_id'),
                'created_at': product.get('created_at')
            }
            
            add_product(product_data)
            products_migrated += 1
            logger.info(f"  ✅ Товар: {product_id} ({product.get('subcategory', '')})")
            
        except Exception as e:
            logger.error(f"  ❌ Ошибка миграции товара {product_id}: {e}")
    
    # Миграция индивидуальных товаров (тушки с точным весом)
    individual_products = old_data.get('individual_products', {})
    individual_migrated = 0
    
    with get_db_connection() as conn:
        for prod_id, prod in individual_products.items():
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO individual_products
                    (id, base_product_id, exact_weight, exact_price, photo_id, is_sold)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    prod_id,
                    prod.get('product_id', prod.get('base_product_id', '')),
                    prod.get('weight', prod.get('exact_weight', 0)),
                    prod.get('price', prod.get('exact_price', 0)),
                    prod.get('photo_id'),
                    prod.get('is_sold', prod.get('status') == 'sold')
                ))
                individual_migrated += 1
            except Exception as e:
                logger.warning(f"  ⚠️ Не удалось мигрировать индивидуальный товар {prod_id}: {e}")
    
    logger.info(f"✅ Мигрировано товаров: {products_migrated}, индивидуальных: {individual_migrated}")
    return products_migrated, individual_migrated


def get_category_id_by_name(category_name):
    """Получить ID категории по названию"""
    category_mapping = {
        '🥚 Яйцо': 1,
        '🍗 Мясо': 2,
        '🥫 Полуфабрикаты': 3,
        '🍿 Снеки': 4
    }
    return category_mapping.get(category_name, 2)  # По умолчанию Мясо


def migrate_orders(old_data):
    """Миграция заказов"""
    logger.info("\n📦 Миграция заказов...")
    
    orders = old_data.get('orders', {})
    orders_migrated = 0
    items_migrated = 0
    
    for order_id, order in orders.items():
        try:
            # Создаем заказ
            order_data = {
                'id': order_id,
                'user_id': int(order.get('user_id', 0)),
                'status': map_order_status(order.get('status', 'new')),
                'total_amount': int(order.get('total', order.get('total_amount', 0))),
                'delivery_cost': int(order.get('delivery_cost', 0)),
                'delivery_method': order.get('delivery_method', 'pickup'),
                'delivery_address': order.get('address', order.get('delivery_address', '')),
                'customer_name': order.get('customer_name', ''),
                'customer_phone': order.get('customer_phone', ''),
                'comment': order.get('comment', ''),
                'created_at': order.get('created_at')
            }
            
            create_order(order_data)
            
            # Добавляем элементы заказа
            for item in order.get('items', []):
                try:
                    add_order_item(
                        order_id,
                        item.get('id', ''),
                        item.get('name', ''),
                        int(item.get('quantity', 1)),
                        int(item.get('price', 0)),
                        int(item.get('total', item.get('price', 0) * item.get('quantity', 1))),
                        weight=item.get('average_weight')
                    )
                    items_migrated += 1
                except Exception as e:
                    logger.warning(f"  ⚠️ Не удалось добавить элемент заказа: {e}")
            
            orders_migrated += 1
            
        except Exception as e:
            logger.error(f"  ❌ Ошибка миграции заказа {order_id}: {e}")
    
    logger.info(f"✅ Мигрировано заказов: {orders_migrated}, элементов: {items_migrated}")
    return orders_migrated, items_migrated


def map_order_status(old_status):
    """Преобразование статуса заказа из старого формата в новый"""
    status_mapping = {
        '🆕 Новый': 'new',
        '✅ Подтвержден': 'confirmed',
        '🚚 В доставке': 'delivering',
        '✅ Выполнен': 'completed',
        '❌ Отменен': 'cancelled',
        '⏰ Перенесен': 'postponed'
    }
    return status_mapping.get(old_status, 'new')


def migrate_notifications(old_data):
    """Миграция подписок на уведомления"""
    logger.info("\n🔔 Миграция подписок на уведомления...")
    
    notifications = old_data.get('notifications', {})
    subscriptions_migrated = 0
    
    with get_db_connection() as conn:
        for product_id, user_list in notifications.items():
            for user_id in user_list:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO notifications (user_id, product_id)
                        VALUES (?, ?)
                    """, (int(user_id), product_id))
                    subscriptions_migrated += 1
                except Exception as e:
                    pass
    
    logger.info(f"✅ Мигрировано подписок: {subscriptions_migrated}")
    return subscriptions_migrated


def migrate_carts(old_data):
    """Миграция корзин (опционально, можно не переносить)"""
    logger.info("\n🛒 Миграция корзин (пропущено)...")
    logger.info("ℹ️ Корзины не мигрируются, так как это временные данные")
    return 0


def migrate_stats(old_data):
    """Миграция статистики пользователей"""
    logger.info("\n📊 Миграция статистики пользователей...")
    
    user_stats = old_data.get('user_stats', {})
    stats_migrated = 0
    
    with get_db_connection() as conn:
        for user_id, stats in user_stats.items():
            try:
                conn.execute("""
                    UPDATE users SET
                        total_orders = ?,
                        total_spent = ?
                    WHERE user_id = ?
                """, (
                    stats.get('total_orders', 0),
                    stats.get('total_spent', 0),
                    int(user_id)
                ))
                stats_migrated += 1
            except Exception as e:
                pass
    
    logger.info(f"✅ Мигрировано статистик: {stats_migrated}")
    return stats_migrated


def migrate_reviews(old_data):
    """Миграция отзывов"""
    logger.info("\n⭐ Миграция отзывов...")
    
    reviews = old_data.get('reviews', {})
    reviews_migrated = 0
    
    with get_db_connection() as conn:
        for product_id, review_list in reviews.items():
            for review in review_list:
                try:
                    conn.execute("""
                        INSERT INTO reviews (product_id, user_id, rating, text, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        product_id,
                        int(review.get('user_id', 0)),
                        int(review.get('rating', 5)),
                        review.get('text', ''),
                        review.get('date', datetime.now().strftime("%d.%m.%Y %H:%M"))
                    ))
                    reviews_migrated += 1
                except Exception as e:
                    pass
    
    logger.info(f"✅ Мигрировано отзывов: {reviews_migrated}")
    return reviews_migrated


def main():
    logger.info("=" * 60)
    logger.info("🚀 МИГРАЦИЯ ДАННЫХ ИЗ СТАРОГО БОТА В НОВЫЙ (SQLite)")
    logger.info("=" * 60)
    
    # 1. Инициализация новой базы
    logger.info("\n1️⃣ Инициализация базы данных SQLite...")
    init_database()
    logger.info("✅ База данных готова")
    
    # 2. Загрузка старых данных
    logger.info("\n2️⃣ Загрузка данных из старого бота...")
    old_data = load_old_data(OLD_DATA_FILE)
    
    if not old_data:
        logger.error("\n❌ Не удалось загрузить старые данные!")
        logger.error("💡 Убедитесь, что файл shop_data.json существует")
        return
    
    # 3. Миграция данных
    logger.info("\n3️⃣ Начало миграции...")
    
    users, admins = migrate_users(old_data)
    products, individual = migrate_products(old_data)
    orders, items = migrate_orders(old_data)
    subscriptions = migrate_notifications(old_data)
    stats = migrate_stats(old_data)
    reviews = migrate_reviews(old_data)
    
    # 4. Итоговый отчет
    logger.info("\n" + "=" * 60)
    logger.info("✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
    logger.info("=" * 60)
    logger.info(f"👥 Пользователей: {users}")
    logger.info(f"👑 Админов: {admins}")
    logger.info(f"🍗 Товаров: {products}")
    logger.info(f"📦 Индивидуальных товаров: {individual}")
    logger.info(f"📋 Заказов: {orders}")
    logger.info(f"🛒 Элементов заказов: {items}")
    logger.info(f"🔔 Подписок на уведомления: {subscriptions}")
    logger.info(f"📊 Статистик пользователей: {stats}")
    logger.info(f"⭐ Отзывов: {reviews}")
    logger.info("=" * 60)
    
    logger.info("\n📊 Следующие шаги:")
    logger.info("   1. Проверьте данные в новом боте")
    logger.info("   2. Запустите нового бота: python bot_test.py")
    logger.info("   3. Убедитесь, что все товары и заказы на месте")
    logger.info("   4. Старого бота можно остановить")
    
    # 5. Создаем бэкап старых данных
    backup_file = f'shop_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(old_data, f, ensure_ascii=False, indent=2)
        logger.info(f"\n💾 Создан бэкап старых данных: {backup_file}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось создать бэкап: {e}")


if __name__ == '__main__':
    main()
