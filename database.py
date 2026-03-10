"""
Модуль работы с SQLite базой данных для Telegram бота
Хранит: товары, заказы, корзины, клиентов, статистику, отзывы, админов
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "shop.db"

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Инициализация базы данных - создание всех таблиц"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица пользователей (клиенты и админы)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                is_blocked BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_orders INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0
            )
        """)
        
        # Таблица адресов доставки пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                address TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Таблица категорий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                unit TEXT DEFAULT 'шт',
                config TEXT,
                sort_order INTEGER DEFAULT 0
            )
        """)
        
        # Таблица товаров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                category_id INTEGER NOT NULL,
                subcategory TEXT NOT NULL,
                subcategory_type TEXT,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                price_per_kg BOOLEAN DEFAULT FALSE,
                average_weight REAL,
                quantity INTEGER DEFAULT 0,
                reserved INTEGER DEFAULT 0,
                photo_id TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                frozen_at TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Таблица индивидуальных товаров (тушки с точным весом)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS individual_products (
                id TEXT PRIMARY KEY,
                base_product_id TEXT NOT NULL,
                exact_weight REAL NOT NULL,
                exact_price INTEGER NOT NULL,
                photo_id TEXT,
                is_sold BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (base_product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        
        # Таблица корзин
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                individual_product_id TEXT,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (individual_product_id) REFERENCES individual_products(id) ON DELETE CASCADE
            )
        """)
        
        # Таблица заказов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'new',
                total_amount INTEGER NOT NULL,
                delivery_cost INTEGER DEFAULT 0,
                delivery_method TEXT DEFAULT 'pickup',
                delivery_address TEXT,
                customer_name TEXT,
                customer_phone TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                completed_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                postponed_to DATE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица элементов заказа
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                individual_product_id TEXT,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                total INTEGER NOT NULL,
                weight REAL,
                returned BOOLEAN DEFAULT FALSE,
                return_reason TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Таблица уведомлений о появлении товара
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        
        # Таблица отзывов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_approved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица просмотров товаров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        
        # Таблица возвратов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                order_item_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                refund_amount INTEGER DEFAULT 0,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (order_item_id) REFERENCES order_items(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица статистики (агрегированные данные)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, metric_name)
            )
        """)
        
        # Таблица настроек бота
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Индексы для ускорения поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_quantity ON products(quantity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_carts_user ON carts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statistics_date ON statistics(date)")
        
        logger.info("✅ База данных инициализирована")


# ==================== ПОЛЬЗОВАТЕЛИ ====================

def add_or_update_user(user_id: int, username: str = None, first_name: str = None, 
                       last_name: str = None, phone: str = None) -> bool:
    """Добавить или обновить информацию о пользователе"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, phone, last_visit)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = COALESCE(excluded.username, users.username),
                first_name = COALESCE(excluded.first_name, users.first_name),
                last_name = COALESCE(excluded.last_name, users.last_name),
                phone = COALESCE(excluded.phone, users.phone),
                last_visit = CURRENT_TIMESTAMP
        """, (user_id, username, first_name, last_name, phone))
    return True


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    """Получить информацию о пользователе"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row is not None and row['is_admin']


def set_admin_status(user_id: int, is_admin: bool) -> bool:
    """Установить статус админа"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO users (user_id, is_admin) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET is_admin = excluded.is_admin
        """, (user_id, is_admin))
    return True


def get_all_admins() -> List[sqlite3.Row]:
    """Получить всех админов"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM users WHERE is_admin = TRUE")
        return cursor.fetchall()


def block_user(user_id: int) -> bool:
    """Заблокировать пользователя"""
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET is_blocked = TRUE WHERE user_id = ?", (user_id,))
    return True


def unblock_user(user_id: int) -> bool:
    """Разблокировать пользователя"""
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET is_blocked = FALSE WHERE user_id = ?", (user_id,))
    return True


def get_all_customers() -> List[sqlite3.Row]:
    """Получить всех клиентов (не админов)"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM users 
            WHERE is_admin = FALSE 
            ORDER BY total_spent DESC, total_orders DESC
        """)
        return cursor.fetchall()


def update_user_stats(user_id: int, order_amount: float) -> bool:
    """Обновить статистику пользователя после заказа"""
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE users 
            SET total_orders = total_orders + 1,
                total_spent = total_spent + ?
            WHERE user_id = ?
        """, (order_amount, user_id))
    return True


# ==================== АДРЕСА ====================

def add_user_address(user_id: int, address: str, name: str, phone: str, 
                     is_default: bool = False) -> int:
    """Добавить адрес пользователя"""
    with get_db_connection() as conn:
        if is_default:
            conn.execute("""
                UPDATE user_addresses SET is_default = FALSE WHERE user_id = ?
            """, (user_id,))
        
        cursor = conn.execute("""
            INSERT INTO user_addresses (user_id, address, name, phone, is_default)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, address, name, phone, is_default))
        return cursor.lastrowid


def get_user_addresses(user_id: int) -> List[sqlite3.Row]:
    """Получить все адреса пользователя"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM user_addresses 
            WHERE user_id = ? 
            ORDER BY is_default DESC, created_at DESC
        """, (user_id,))
        return cursor.fetchall()


def get_default_address(user_id: int) -> Optional[sqlite3.Row]:
    """Получить адрес по умолчанию"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM user_addresses 
            WHERE user_id = ? AND is_default = TRUE
        """, (user_id,))
        return cursor.fetchone()


def delete_user_address(user_id: int, address_id: int) -> bool:
    """Удалить адрес пользователя"""
    with get_db_connection() as conn:
        conn.execute("""
            DELETE FROM user_addresses 
            WHERE user_id = ? AND id = ?
        """, (user_id, address_id))
        return conn.total_changes > 0


# ==================== ТОВАРЫ ====================

def add_product(product_data: dict) -> bool:
    """Добавить товар"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO products 
            (id, category_id, subcategory, subcategory_type, name, description, 
             price, price_per_kg, average_weight, quantity, photo_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_data['id'],
            product_data['category_id'],
            product_data['subcategory'],
            product_data.get('subcategory_type'),
            product_data['name'],
            product_data.get('description'),
            product_data['price'],
            product_data.get('price_per_kg', False),
            product_data.get('average_weight'),
            product_data.get('quantity', 0),
            product_data.get('photo_id')
        ))
    return True


def get_product(product_id: str) -> Optional[sqlite3.Row]:
    """Получить товар по ID"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT p.*, c.name as category_name, c.display_name, c.unit
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        """, (product_id,))
        return cursor.fetchone()


def get_all_products(active_only: bool = False) -> List[sqlite3.Row]:
    """Получить все товары"""
    with get_db_connection() as conn:
        query = """
            SELECT p.*, c.name as category_name, c.display_name, c.unit
            FROM products p
            JOIN categories c ON p.category_id = c.id
        """
        if active_only:
            query += " WHERE p.is_active = TRUE AND p.quantity > 0"
        query += " ORDER BY p.created_at DESC"
        
        cursor = conn.execute(query)
        return cursor.fetchall()


def get_products_by_category(category_id: int, active_only: bool = False) -> List[sqlite3.Row]:
    """Получить товары по категории"""
    with get_db_connection() as conn:
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.category_id = ?
        """
        if active_only:
            query += " AND p.is_active = TRUE AND p.quantity > 0"
        query += " ORDER BY p.created_at DESC"
        
        cursor = conn.execute(query, (category_id,))
        return cursor.fetchall()


def update_product(product_id: str, update_data: dict) -> bool:
    """Обновить товар"""
    if not update_data:
        return False
    
    update_data['updated_at'] = datetime.now()
    update_data['id'] = product_id
    
    with get_db_connection() as conn:
        set_clause = ', '.join(f"{key} = ?" for key in update_data.keys() if key != 'id')
        query = f"UPDATE products SET {set_clause} WHERE id = ?"
        
        values = [v for k, v in update_data.items() if k != 'id'] + [product_id]
        cursor = conn.execute(query, values)
        return cursor.rowcount > 0


def delete_product(product_id: str) -> bool:
    """Удалить товар"""
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        return cursor.rowcount > 0


def update_product_quantity(product_id: str, quantity: int) -> bool:
    """Обновить количество товара"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            UPDATE products 
            SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (quantity, product_id))
        return cursor.rowcount > 0


def reserve_product_quantity(product_id: str, quantity: int) -> bool:
    """Зарезервировать количество товара (для корзины/заказа)"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            UPDATE products 
            SET reserved = reserved + ? 
            WHERE id = ? AND (quantity - reserved) >= ?
        """, (quantity, product_id, quantity))
        return cursor.rowcount > 0


def release_product_quantity(product_id: str, quantity: int) -> bool:
    """Снять резерв с товара"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            UPDATE products 
            SET reserved = MAX(0, reserved - ?),
                quantity = MAX(0, quantity - ?)
            WHERE id = ?
        """, (quantity, quantity, product_id))
        return cursor.rowcount > 0


def get_low_stock_products(threshold: int = 5) -> List[sqlite3.Row]:
    """Получить товары с низким остатком"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM products 
            WHERE quantity <= ? AND is_active = TRUE
            ORDER BY quantity ASC
        """, (threshold,))
        return cursor.fetchall()


# ==================== ИНДИВИДУАЛЬНЫЕ ТОВАРА ====================

def add_individual_product(product_data: dict) -> bool:
    """Добавить индивидуальный товар (тушку с точным весом)"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO individual_products 
            (id, base_product_id, exact_weight, exact_price, photo_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            product_data['id'],
            product_data['base_product_id'],
            product_data['exact_weight'],
            product_data['exact_price'],
            product_data.get('photo_id')
        ))
    return True


def get_individual_product(product_id: str) -> Optional[sqlite3.Row]:
    """Получить индивидуальный товар"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT ip.*, p.name as base_product_name
            FROM individual_products ip
            JOIN products p ON ip.base_product_id = p.id
            WHERE ip.id = ?
        """, (product_id,))
        return cursor.fetchone()


def get_individual_products_by_base(base_product_id: str, 
                                     available_only: bool = False) -> List[sqlite3.Row]:
    """Получить все индивидуальные товары для базового товара"""
    with get_db_connection() as conn:
        query = """
            SELECT ip.*, p.name as base_product_name
            FROM individual_products ip
            JOIN products p ON ip.base_product_id = p.id
            WHERE ip.base_product_id = ?
        """
        if available_only:
            query += " AND ip.is_sold = FALSE"
        
        cursor = conn.execute(query, (base_product_id,))
        return cursor.fetchall()


def mark_individual_product_sold(product_id: str) -> bool:
    """Отметить индивидуальный товар как проданный"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            UPDATE individual_products 
            SET is_sold = TRUE 
            WHERE id = ?
        """, (product_id,))
        return cursor.rowcount > 0


def delete_individual_product(product_id: str) -> bool:
    """Удалить индивидуальный товар"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM individual_products WHERE id = ?
        """, (product_id,))
        return cursor.rowcount > 0


# ==================== КОРЗИНА ====================

def add_to_cart(user_id: int, product_id: str, quantity: int = 1, 
                individual_product_id: str = None) -> bool:
    """Добавить товар в корзину"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO carts (user_id, product_id, individual_product_id, quantity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, product_id, individual_product_id) 
            DO UPDATE SET quantity = carts.quantity + ?,
                          added_at = CURRENT_TIMESTAMP
        """, (user_id, product_id, individual_product_id, quantity, quantity))
    return True


def get_cart(user_id: int) -> List[sqlite3.Row]:
    """Получить корзину пользователя"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT c.*, p.name, p.price, p.price_per_kg, p.average_weight,
                   ip.exact_weight, ip.exact_price
            FROM carts c
            JOIN products p ON c.product_id = p.id
            LEFT JOIN individual_products ip ON c.individual_product_id = ip.id
            WHERE c.user_id = ?
            ORDER BY c.added_at DESC
        """, (user_id,))
        return cursor.fetchall()


def update_cart_item_quantity(user_id: int, product_id: str, quantity: int,
                               individual_product_id: str = None) -> bool:
    """Обновить количество товара в корзине"""
    with get_db_connection() as conn:
        if individual_product_id:
            cursor = conn.execute("""
                UPDATE carts SET quantity = ?
                WHERE user_id = ? AND product_id = ? AND individual_product_id = ?
            """, (quantity, user_id, product_id, individual_product_id))
        else:
            cursor = conn.execute("""
                UPDATE carts SET quantity = ?
                WHERE user_id = ? AND product_id = ? AND (individual_product_id IS NULL OR individual_product_id = '')
            """, (quantity, user_id, product_id))
        return cursor.rowcount > 0


def remove_from_cart(user_id: int, product_id: str, 
                     individual_product_id: str = None) -> bool:
    """Удалить товар из корзины"""
    with get_db_connection() as conn:
        if individual_product_id:
            cursor = conn.execute("""
                DELETE FROM carts 
                WHERE user_id = ? AND product_id = ? AND individual_product_id = ?
            """, (user_id, product_id, individual_product_id))
        else:
            cursor = conn.execute("""
                DELETE FROM carts 
                WHERE user_id = ? AND product_id = ? 
                AND (individual_product_id IS NULL OR individual_product_id = '')
            """, (user_id, product_id))
        return cursor.rowcount > 0


def clear_cart(user_id: int) -> bool:
    """Очистить корзину пользователя"""
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0


def get_cart_count(user_id: int) -> int:
    """Получить количество товаров в корзине"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT COALESCE(SUM(quantity), 0) as total
            FROM carts WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        return row['total'] if row else 0


# ==================== ЗАКАЗЫ ====================

def create_order(order_data: dict) -> str:
    """Создать заказ"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO orders 
            (id, user_id, status, total_amount, delivery_cost, delivery_method,
             delivery_address, customer_name, customer_phone, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_data['id'],
            order_data['user_id'],
            order_data.get('status', 'new'),
            order_data['total_amount'],
            order_data.get('delivery_cost', 0),
            order_data.get('delivery_method', 'pickup'),
            order_data.get('delivery_address'),
            order_data.get('customer_name'),
            order_data.get('customer_phone'),
            order_data.get('comment')
        ))
    return order_data['id']


def add_order_item(order_id: str, product_id: str, product_name: str,
                   quantity: int, price: int, total: int,
                   individual_product_id: str = None, weight: float = None) -> bool:
    """Добавить элемент заказа"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO order_items 
            (order_id, product_id, product_name, individual_product_id,
             quantity, price, total, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, product_id, product_name, individual_product_id,
              quantity, price, total, weight))
    return True


def get_order(order_id: str) -> Optional[sqlite3.Row]:
    """Получить заказ"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT o.*, u.first_name, u.last_name, u.username
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            WHERE o.id = ?
        """, (order_id,))
        return cursor.fetchone()


def get_order_items(order_id: str) -> List[sqlite3.Row]:
    """Получить элементы заказа"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM order_items WHERE order_id = ?
        """, (order_id,))
        return cursor.fetchall()


def get_user_orders(user_id: int, limit: int = None) -> List[sqlite3.Row]:
    """Получить заказы пользователя"""
    with get_db_connection() as conn:
        query = """
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = conn.execute(query, (user_id,))
        return cursor.fetchall()


def get_orders_by_status(status: str) -> List[sqlite3.Row]:
    """Получить заказы по статусу"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT o.*, u.first_name, u.last_name, u.username, u.phone as user_phone
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            WHERE o.status = ?
            ORDER BY o.created_at DESC
        """, (status,))
        return cursor.fetchall()


def get_all_orders(limit: int = 100) -> List[sqlite3.Row]:
    """Получить все заказы"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT o.*, u.first_name, u.last_name, u.username
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            ORDER BY o.created_at DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()


def update_order_status(order_id: str, status: str) -> bool:
    """Обновить статус заказа"""
    with get_db_connection() as conn:
        update_data = {'status': status, 'updated_at': datetime.now()}
        
        if status == 'paid':
            update_data['paid_at'] = datetime.now()
        elif status == 'completed':
            update_data['completed_at'] = datetime.now()
        elif status == 'cancelled':
            update_data['cancelled_at'] = datetime.now()
        
        set_clause = ', '.join(f"{key} = ?" for key in update_data.keys())
        values = list(update_data.values()) + [order_id]
        
        cursor = conn.execute(f"UPDATE orders SET {set_clause} WHERE id = ?", values)
        return cursor.rowcount > 0


def postpone_order(order_id: str, new_date: datetime) -> bool:
    """Перенести заказ"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            UPDATE orders 
            SET postponed_to = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_date.date(), order_id))
        return cursor.rowcount > 0


def get_postponed_orders() -> List[sqlite3.Row]:
    """Получить перенесенные заказы"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM orders 
            WHERE postponed_to IS NOT NULL AND postponed_to >= date('now')
            ORDER BY postponed_to ASC
        """)
        return cursor.fetchall()


# ==================== УВЕДОМЛЕНИЯ ====================

def add_notification(user_id: int, product_id: str) -> bool:
    """Добавить уведомление о появлении товара"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO notifications (user_id, product_id)
            VALUES (?, ?)
            ON CONFLICT(user_id, product_id) DO NOTHING
        """, (user_id, product_id))
    return True


def get_user_notifications(user_id: int) -> List[sqlite3.Row]:
    """Получить уведомления пользователя"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT n.*, p.name as product_name
            FROM notifications n
            JOIN products p ON n.product_id = p.id
            WHERE n.user_id = ? AND n.sent = FALSE
        """, (user_id,))
        return cursor.fetchall()


def mark_notification_sent(notification_id: int) -> bool:
    """Отметить уведомление как отправленное"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            UPDATE notifications SET sent = TRUE WHERE id = ?
        """, (notification_id,))
        return cursor.rowcount > 0


def remove_notification(user_id: int, product_id: str) -> bool:
    """Удалить уведомление"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM notifications 
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))
        return cursor.rowcount > 0


# ==================== ОТЗЫВЫ ====================

def add_review(product_id: str, user_id: int, rating: int, 
               text: str = None) -> int:
    """Добавить отзыв"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO reviews (product_id, user_id, rating, text)
            VALUES (?, ?, ?, ?)
        """, (product_id, user_id, rating, text))
        return cursor.lastrowid


def get_product_reviews(product_id: str, approved_only: bool = False) -> List[sqlite3.Row]:
    """Получить отзывы о товаре"""
    with get_db_connection() as conn:
        query = """
            SELECT r.*, u.first_name, u.last_name, u.username
            FROM reviews r
            LEFT JOIN users u ON r.user_id = u.user_id
            WHERE r.product_id = ?
        """
        if approved_only:
            query += " AND r.is_approved = TRUE"
        query += " ORDER BY r.created_at DESC"
        
        cursor = conn.execute(query, (product_id,))
        return cursor.fetchall()


def get_product_rating(product_id: str) -> Optional[float]:
    """Получить средний рейтинг товара"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as count
            FROM reviews WHERE product_id = ?
        """, (product_id,))
        row = cursor.fetchone()
        return row['avg_rating'] if row and row['count'] > 0 else None


def approve_review(review_id: int) -> bool:
    """Одобрить отзыв"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            UPDATE reviews SET is_approved = TRUE WHERE id = ?
        """, (review_id,))
        return cursor.rowcount > 0


def delete_review(review_id: int) -> bool:
    """Удалить отзыв"""
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        return cursor.rowcount > 0


# ==================== ПРОСМОТРЫ ====================

def log_product_view(user_id: int, product_id: str) -> bool:
    """Записать просмотр товара"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO product_views (user_id, product_id)
            VALUES (?, ?)
        """, (user_id, product_id))
    return True


def get_product_views_count(product_id: str) -> int:
    """Получить количество просмотров товара"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM product_views WHERE product_id = ?
        """, (product_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0


# ==================== ВОЗВРАТЫ ====================

def create_return(order_id: str, order_item_id: int, user_id: int, 
                  reason: str) -> int:
    """Создать возврат"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO returns (order_id, order_item_id, user_id, reason)
            VALUES (?, ?, ?, ?)
        """, (order_id, order_item_id, user_id, reason))
        return cursor.lastrowid


def get_order_returns(order_id: str) -> List[sqlite3.Row]:
    """Получить возвраты по заказу"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT r.*, oi.product_name, oi.total as item_total
            FROM returns r
            JOIN order_items oi ON r.order_item_id = oi.id
            WHERE r.order_id = ?
        """, (order_id,))
        return cursor.fetchall()


def update_return_status(return_id: int, status: str, 
                         refund_amount: int = 0) -> bool:
    """Обновить статус возврата"""
    with get_db_connection() as conn:
        update_data = {
            'status': status,
            'resolved_at': datetime.now(),
            'refund_amount': refund_amount
        }
        set_clause = ', '.join(f"{key} = ?" for key in update_data.keys())
        values = list(update_data.values()) + [return_id]
        
        cursor = conn.execute(f"UPDATE returns SET {set_clause} WHERE id = ?", values)
        return cursor.rowcount > 0


# ==================== СТАТИСТИКА ====================

def save_daily_statistic(date: str, metric_name: str, metric_value: float,
                         metadata: dict = None) -> bool:
    """Сохранить дневную статистику"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO statistics (date, metric_name, metric_value, metadata)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date, metric_name) 
            DO UPDATE SET metric_value = excluded.metric_value,
                          metadata = excluded.metadata
        """, (date, metric_name, metric_value, 
              json.dumps(metadata) if metadata else None))
    return True


def get_statistics(date_from: datetime = None, 
                   date_to: datetime = None) -> List[sqlite3.Row]:
    """Получить статистику за период"""
    with get_db_connection() as conn:
        query = "SELECT * FROM statistics WHERE 1=1"
        params = []
        
        if date_from:
            query += " AND date >= ?"
            params.append(date_from.date())
        if date_to:
            query += " AND date <= ?"
            params.append(date_to.date())
        
        query += " ORDER BY date DESC"
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def get_sales_statistics(days: int = 30) -> Dict[str, Any]:
    """Получить статистику продаж"""
    with get_db_connection() as conn:
        # Общая выручка
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(AVG(total_amount), 0) as avg_order_value
            FROM orders
            WHERE status NOT IN ('cancelled')
            AND created_at >= datetime('now', ? || ' days')
        """, (f'-{days}',))
        summary = cursor.fetchone()
        
        # По категориям
        cursor = conn.execute("""
            SELECT c.name as category, 
                   COUNT(oi.id) as items_sold,
                   COALESCE(SUM(oi.total), 0) as revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status NOT IN ('cancelled')
            AND o.created_at >= datetime('now', ? || ' days')
            GROUP BY c.id, c.name
        """, (f'-{days}',))
        by_category = cursor.fetchall()
        
        # По дням
        cursor = conn.execute("""
            SELECT date(created_at) as date,
                   COUNT(*) as orders_count,
                   COALESCE(SUM(total_amount), 0) as revenue
            FROM orders
            WHERE status NOT IN ('cancelled')
            AND created_at >= datetime('now', ? || ' days')
            GROUP BY date(created_at)
            ORDER BY date DESC
        """, (f'-{days}',))
        by_day = cursor.fetchall()
        
        return {
            'summary': dict(summary) if summary else {},
            'by_category': [dict(row) for row in by_category],
            'by_day': [dict(row) for row in by_day]
        }


def get_top_products(days: int = 30, limit: int = 10) -> List[sqlite3.Row]:
    """Получить топ популярных товаров"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT p.id, p.name, c.name as category,
                   SUM(oi.quantity) as total_sold,
                   COALESCE(SUM(oi.total), 0) as total_revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status NOT IN ('cancelled')
            AND o.created_at >= datetime('now', ? || ' days')
            GROUP BY p.id, p.name, c.name
            ORDER BY total_sold DESC
            LIMIT ?
        """, (f'-{days}', limit))
        return cursor.fetchall()


def get_top_customers(days: int = 30, limit: int = 10) -> List[sqlite3.Row]:
    """Получить топ клиентов"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT u.user_id, u.first_name, u.last_name, u.username,
                   COUNT(o.id) as orders_count,
                   COALESCE(SUM(o.total_amount), 0) as total_spent
            FROM users u
            JOIN orders o ON u.user_id = o.user_id
            WHERE o.status NOT IN ('cancelled')
            AND o.created_at >= datetime('now', ? || ' days')
            GROUP BY u.user_id, u.first_name, u.last_name, u.username
            ORDER BY total_spent DESC
            LIMIT ?
        """, (f'-{days}', limit))
        return cursor.fetchall()


# ==================== НАСТРОЙКИ ====================

def get_setting(key: str, default: Any = None) -> Any:
    """Получить настройку"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row['value'])
            except:
                return row['value']
        return default


def set_setting(key: str, value: Any) -> bool:
    """Установить настройку"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET 
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
        """, (key, json.dumps(value) if not isinstance(value, str) else value))
    return True


# ==================== ИНИЦИАЛИЗАЦИЯ КАТЕГОРИЙ ====================

def init_categories():
    """Инициализация категорий из CATEGORIES"""
    # Импортируем CATEGORIES напрямую, чтобы избежать циклического импорта
    CATEGORIES_LOCAL = {
        "🥚 Яйцо": {
            "name": "🥚 Яйцо",
            "subcategories": ["🐔 Куриное", "🐦 Перепелиное", "👑 Цесариное"],
            "unit": "шт",
            "multiplier": {
                "🐔 Куриное": 10,
                "🐦 Перепелиное": 20,
                "👑 Цесариное": 10
            },
            "exact_price": True
        },
        "🍗 Мясо": {
            "name": "🍗 Мясо",
            "subcategories": {
                "❄️ Охлажденное": {
                    "Тушки": [
                        "🐓 Цыпленок бройлер",
                        "🐔 Молодой петушок",
                        "👑 Цесарка",
                        "🐦 Перепелка"
                    ],
                    "🥩 Частями": [
                        "🍗 Грудка",
                        "🍗 Окорочка",
                        "🍗 Крылья",
                        "🍗 Спинки"
                    ],
                    "🥣 Потроха": [
                        "❤️ Сердце",
                        "🫔 Печень",
                        "🦴 Шея"
                    ],
                    "🥩 Фарш": [
                        "Фарш 60/40",
                        "Фарш 100% грудка"
                    ]
                },
                "🧊 Замороженное": {
                    "Тушки": [
                        "🐓 Цыпленок бройлер",
                        "🐔 Молодой петушок",
                        "👑 Цесарка",
                        "🐦 Перепелка"
                    ],
                    "🥩 Частями": [
                        "🍗 Грудка",
                        "🍗 Окорочка",
                        "🍗 Крылья",
                        "🍗 Спинки"
                    ],
                    "🥣 Потроха": [
                        "❤️ Сердце",
                        "🫔 Печень",
                        "🦴 Шея"
                    ],
                    "🥩 Фарш": [
                        "Фарш 60/40",
                        "Фарш 100% грудка"
                    ]
                }
            },
            "unit": "кг",
            "price_per_kg": True,
            "average_weight": {
                "🐓 Цыпленок бройлер": 2.5,
                "🐔 Молодой петушок": 1,
                "👑 Цесарка": 1.4,
                "🐦 Перепелка": 0.2
            },
            "parts_weight": {
                "🍗 Грудка": 0.4,
                "🍗 Окорочка": 1.2,
                "🍗 Крылья": 0.8,
                "🍗 Спинки": 0.5,
                "❤️ Сердце": 0.5,
                "🫔 Печень": 0.5,
                "🦴 Шея": 1.0
            },
            "parts_packaging": {
                "🍗 Грудка": {"unit": "упак", "qty": 1},
                "🍗 Окорочка": {"unit": "упак", "qty": 3},
                "🍗 Крылья": {"unit": "упак", "qty": 8},
                "🍗 Спинки": {"unit": "упак", "qty": 1},
                "❤️ Сердце": {"unit": "упак", "weight": 0.5},
                "🫔 Печень": {"unit": "упак", "weight": 0.5},
                "🦴 Шея": {"unit": "шт", "qty": 1}
            },
            "minced_step": 0.1,
            "exact_price": False,
            "freeze_delay_hours": 48
        },
        "🥫 Полуфабрикаты": {
            "name": "🥫 Полуфабрикаты",
            "subcategories": ["🌭 Колбаса", "🥩 Тушенка"],
            "unit": "шт",
            "price_per_kg": True,
            "average_weight": {
                "🌭 Колбаса": 0.4,
                "🥩 Тушенка": 0.5
            },
            "exact_price": False
        },
        "🍿 Снеки": {
            "name": "🍿 Снеки",
            "subcategories": ["Колбаски"],
            "unit": "шт",
            "price_per_kg": True,
            "average_weight": {
                "Колбаски": 0.1  # 100гр за штуку
            },
            "exact_price": False
        }
    }
    
    with get_db_connection() as conn:
        for idx, (cat_name, cat_data) in enumerate(CATEGORIES_LOCAL.items()):
            config = {
                'subcategories': cat_data.get('subcategories'),
                'unit': cat_data.get('unit', 'шт'),
                'multiplier': cat_data.get('multiplier'),
                'price_per_kg': cat_data.get('price_per_kg', False),
                'average_weight': cat_data.get('average_weight'),
                'parts_weight': cat_data.get('parts_weight'),
                'parts_packaging': cat_data.get('parts_packaging'),
                'minced_step': cat_data.get('minced_step'),
                'exact_price': cat_data.get('exact_price', True),
                'freeze_delay_hours': cat_data.get('freeze_delay_hours')
            }
            
            conn.execute("""
                INSERT OR REPLACE INTO categories 
                (name, display_name, unit, config, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (cat_name, cat_data['name'], cat_data.get('unit', 'шт'),
                  json.dumps(config, ensure_ascii=False), idx))


# ==================== МИГРАЦИЯ ДАННЫХ ====================

def migrate_from_json(json_file: str = 'shop_data.json'):
    """Миграция данных из JSON файла в SQLite"""
    import os
    
    if not os.path.exists(json_file):
        logger.warning(f"Файл {json_file} не найден")
        return False
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with get_db_connection() as conn:
            # Миграция товаров
            products = data.get('products', {})
            for product_id, product in products.items():
                # Получаем category_id из названия категории
                cat_name = product.get('category', '')
                cursor = conn.execute("""
                    SELECT id FROM categories WHERE name = ?
                """, (cat_name,))
                cat_row = cursor.fetchone()
                category_id = cat_row['id'] if cat_row else 1
                
                conn.execute("""
                    INSERT OR REPLACE INTO products
                    (id, category_id, subcategory, subcategory_type, name, 
                     price, price_per_kg, average_weight, quantity, photo_id,
                     created_at, frozen_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id,
                    category_id,
                    product.get('subcategory', ''),
                    product.get('subcategory_type'),
                    product.get('name', ''),
                    product.get('price', 0),
                    product.get('price_per_kg', False),
                    product.get('average_weight'),
                    product.get('quantity', 0),
                    product.get('photo_id'),
                    product.get('created_at'),
                    product.get('frozen_at')
                ))
            
            # Миграция индивидуальных товаров
            individual = data.get('individual_products', {})
            for prod_id, prod in individual.items():
                conn.execute("""
                    INSERT OR REPLACE INTO individual_products
                    (id, base_product_id, exact_weight, exact_price, photo_id, is_sold)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    prod_id,
                    prod.get('base_product_id', ''),
                    prod.get('exact_weight', 0),
                    prod.get('exact_price', 0),
                    prod.get('photo_id'),
                    prod.get('is_sold', False)
                ))
            
            # Миграция заказов
            orders = data.get('orders', {})
            for order_id, order in orders.items():
                conn.execute("""
                    INSERT OR REPLACE INTO orders
                    (id, user_id, status, total_amount, delivery_cost, 
                     delivery_method, delivery_address, customer_name, 
                     customer_phone, comment, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id,
                    order.get('user_id', 0),
                    order.get('status', 'new'),
                    order.get('total_amount', 0),
                    order.get('delivery_cost', 0),
                    order.get('delivery_method', 'pickup'),
                    order.get('delivery_address'),
                    order.get('customer_name'),
                    order.get('customer_phone'),
                    order.get('comment'),
                    order.get('created_at')
                ))
                
                # Элементы заказа
                for item in order.get('items', []):
                    conn.execute("""
                        INSERT INTO order_items
                        (order_id, product_id, product_name, quantity, price, total)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        order_id,
                        item.get('id', ''),
                        item.get('name', ''),
                        item.get('quantity', 1),
                        item.get('price', 0),
                        item.get('total', 0)
                    ))
            
            # Миграция админов
            admins = data.get('admins', [])
            for admin_id in admins:
                conn.execute("""
                    INSERT OR REPLACE INTO users (user_id, is_admin)
                    VALUES (?, TRUE)
                """, (admin_id,))
            
            logger.info("✅ Миграция данных завершена")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        return False


# ==================== ЭКСПОРТ ДАННЫХ ====================

def export_to_json(json_file: str = 'shop_data_backup.json'):
    """Экспорт данных в JSON (для бэкапа)"""
    with get_db_connection() as conn:
        data = {
            'exported_at': datetime.now().isoformat(),
            'products': {},
            'orders': {},
            'users': [],
            'reviews': []
        }
        
        # Товары
        cursor = conn.execute("SELECT * FROM products")
        for row in cursor.fetchall():
            data['products'][row['id']] = dict(row)
        
        # Заказы
        cursor = conn.execute("SELECT * FROM orders")
        for row in cursor.fetchall():
            order_id = row['id']
            data['orders'][order_id] = dict(row)
            data['orders'][order_id]['items'] = [
                dict(item) for item in get_order_items(order_id)
            ]
        
        # Пользователи
        cursor = conn.execute("SELECT * FROM users")
        data['users'] = [dict(row) for row in cursor.fetchall()]
        
        # Отзывы
        cursor = conn.execute("SELECT * FROM reviews")
        data['reviews'] = [dict(row) for row in cursor.fetchall()]
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"✅ Данные экспортированы в {json_file}")
        return True


# Инициализация при импорте
init_database()
logger.info("🗄️ Модуль базы данных загружен")
