"""
Модуль статистики и аналитики для бота
Использует SQLite для быстрых SQL-запросов
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from database import get_db_connection, get_sales_statistics, get_top_products, get_top_customers

logger = logging.getLogger(__name__)


def get_full_statistics(days: int = 30) -> Dict[str, Any]:
    """
    Получить полную статистику за период
    
    Args:
        days: Количество дней для статистики
        
    Returns:
        Dict с полной статистикой
    """
    stats = get_sales_statistics(days)
    
    # Дополняем данными
    with get_db_connection() as conn:
        # Количество новых пользователей
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM users
            WHERE created_at >= datetime('now', ? || ' days')
        """, (f'-{days}',))
        new_users = cursor.fetchone()['count']
        
        # Средний чек
        cursor = conn.execute("""
            SELECT AVG(total_amount) as avg_check
            FROM orders
            WHERE status NOT IN ('cancelled')
            AND created_at >= datetime('now', ? || ' days')
        """, (f'-{days}',))
        avg_check = cursor.fetchone()['avg_check'] or 0
        
        # Конверсия (заказы / пользователи)
        cursor = conn.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as active_customers,
                COUNT(*) as total_orders
            FROM orders
            WHERE created_at >= datetime('now', ? || ' days')
        """, (f'-{days}',))
        row = cursor.fetchone()
        active_customers = row['active_customers'] or 0
        total_orders = row['total_orders'] or 0
        conversion = (total_orders / active_customers * 100) if active_customers > 0 else 0
        
        # Топ товаров
        top_products = [dict(row) for row in get_top_products(days, limit=5)]
        
        # Топ клиентов
        top_customers = [dict(row) for row in get_top_customers(days, limit=5)]
        
        # Статусы заказов
        cursor = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM orders
            WHERE created_at >= datetime('now', ? || ' days')
            GROUP BY status
        """, (f'-{days}',))
        orders_by_status = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Товары с низким остатком
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM products
            WHERE quantity <= 5 AND is_active = TRUE
        """)
        low_stock = cursor.fetchone()['count']
        
    return {
        'summary': stats.get('summary', {}),
        'by_category': stats.get('by_category', []),
        'by_day': stats.get('by_day', []),
        'new_users': new_users,
        'avg_check': avg_check,
        'active_customers': active_customers,
        'total_orders': total_orders,
        'conversion': conversion,
        'top_products': top_products,
        'top_customers': top_customers,
        'orders_by_status': orders_by_status,
        'low_stock_count': low_stock
    }


def format_statistics_report(stats: Dict[str, Any]) -> str:
    """
    Сформировать текстовый отчет по статистике
    """
    summary = stats.get('summary', {})
    
    report = "📊 <b>Статистика за последние 30 дней</b>\n\n"
    
    # Основные метрики
    report += "<b>📈 Основные показатели:</b>\n"
    report += f"• Выручка: {summary.get('total_revenue', 0):.0f} руб.\n"
    report += f"• Заказов: {summary.get('total_orders', 0)}\n"
    report += f"• Средний чек: {stats.get('avg_check', 0):.0f} руб.\n"
    report += f"• Активных клиентов: {stats.get('active_customers', 0)}\n"
    report += f"• Новых пользователей: {stats.get('new_users', 0)}\n"
    report += f"• Конверсия: {stats.get('conversion', 0):.1f}%\n\n"
    
    # По категориям
    report += "<b>📦 Продажи по категориям:</b>\n"
    for cat in stats.get('by_category', [])[:5]:
        cat_dict = dict(cat) if hasattr(cat, 'keys') else cat
        report += f"• {cat_dict.get('category', 'Неизвестно')}: "
        report += f"{cat_dict.get('items_sold', 0)} шт. "
        report += f"({cat_dict.get('revenue', 0):.0f} руб.)\n"
    
    # Топ товаров
    report += "\n<b>🏆 Топ товаров:</b>\n"
    for prod in stats.get('top_products', [])[:5]:
        prod_dict = dict(prod) if hasattr(prod, 'keys') else prod
        report += f"• {prod_dict.get('name', 'Неизвестно')}: "
        report += f"{prod_dict.get('total_sold', 0)} шт.\n"
    
    # Топ клиентов
    report += "\n<b>👑 Топ клиентов:</b>\n"
    for cust in stats.get('top_customers', [])[:5]:
        cust_dict = dict(cust) if hasattr(cust, 'keys') else cust
        name = cust_dict.get('first_name') or cust_dict.get('username') or 'Аноним'
        report += f"• {name}: {cust_dict.get('total_spent', 0):.0f} руб.\n"
    
    # Предупреждения
    if stats.get('low_stock_count', 0) > 0:
        report += f"\n⚠️ <b>Товаров с низким остатком: {stats.get('low_stock_count')}</b>\n"
    
    return report


def get_daily_report(date: datetime = None) -> Dict[str, Any]:
    """
    Получить ежедневный отчет
    
    Args:
        date: Дата отчета (по умолчанию сегодня)
        
    Returns:
        Dict с данными за день
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        # Заказы за день
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as orders,
                COALESCE(SUM(total_amount), 0) as revenue,
                COALESCE(AVG(total_amount), 0) as avg_check
            FROM orders
            WHERE date(created_at) = ?
            AND status NOT IN ('cancelled')
        """, (date_str,))
        summary = cursor.fetchone()
        
        # Новые пользователи
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM users
            WHERE date(created_at) = ?
        """, (date_str,))
        new_users = cursor.fetchone()['count']
        
        # Выполненные заказы
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM orders
            WHERE date(completed_at) = ?
            AND status = 'completed'
        """, (date_str,))
        completed = cursor.fetchone()['count']
        
    return {
        'date': date_str,
        'orders': summary['orders'] if summary else 0,
        'revenue': summary['revenue'] if summary else 0,
        'avg_check': summary['avg_check'] if summary else 0,
        'new_users': new_users,
        'completed_orders': completed
    }


def format_daily_report(data: Dict[str, Any]) -> str:
    """
    Сформировать текст ежедневного отчета
    """
    report = f"📅 <b>Ежедневный отчет</b>\n"
    report += f"🗓️ {data.get('date', 'Неизвестно')}\n\n"
    
    report += "<b>📊 Показатели за день:</b>\n"
    report += f"• Заказов: {data.get('orders', 0)}\n"
    report += f"• Выручка: {data.get('revenue', 0):.0f} руб.\n"
    report += f"• Средний чек: {data.get('avg_check', 0):.0f} руб.\n"
    report += f"• Новых пользователей: {data.get('new_users', 0)}\n"
    report += f"• Выполнено заказов: {data.get('completed_orders', 0)}\n"
    
    return report


def get_inventory_status() -> Dict[str, Any]:
    """
    Получить статус инвентаря
    
    Returns:
        Dict со статусом товаров
    """
    with get_db_connection() as conn:
        # Всего товаров
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(quantity) as total_quantity,
                SUM(reserved) as total_reserved
            FROM products
            WHERE is_active = TRUE
        """)
        total = cursor.fetchone()
        
        # По категориям
        cursor = conn.execute("""
            SELECT 
                c.name as category,
                COUNT(p.id) as products_count,
                SUM(p.quantity) as total_quantity
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE
            GROUP BY c.id, c.name
        """)
        by_category = cursor.fetchall()
        
        # Низкий остаток
        cursor = conn.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.quantity <= 5 AND p.is_active = TRUE
            ORDER BY p.quantity ASC
            LIMIT 10
        """)
        low_stock = cursor.fetchall()
        
        # Нет в наличии
        cursor = conn.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.quantity = 0 AND p.is_active = TRUE
            LIMIT 10
        """)
        out_of_stock = cursor.fetchall()
        
    return {
        'total_products': total['total'] if total else 0,
        'total_quantity': total['total_quantity'] if total else 0,
        'total_reserved': total['total_reserved'] if total else 0,
        'by_category': [dict(row) for row in by_category],
        'low_stock': [dict(row) for row in low_stock],
        'out_of_stock': [dict(row) for row in out_of_stock]
    }


def format_inventory_report(inventory: Dict[str, Any]) -> str:
    """
    Сформировать текст отчета по инвентарю
    """
    report = "📦 <b>Статус инвентаря</b>\n\n"
    
    report += "<b>📊 Общее:</b>\n"
    report += f"• Товаров: {inventory.get('total_products', 0)}\n"
    report += f"• Всего единиц: {inventory.get('total_quantity', 0)}\n"
    report += f"• Зарезервировано: {inventory.get('total_reserved', 0)}\n\n"
    
    report += "<b>📁 По категориям:</b>\n"
    for cat in inventory.get('by_category', []):
        report += f"• {cat.get('category', 'Неизвестно')}: "
        report += f"{cat.get('products_count', 0)} тов., "
        report += f"{cat.get('total_quantity', 0)} шт.\n"
    
    low_stock = inventory.get('low_stock', [])
    if low_stock:
        report += f"\n⚠️ <b>Заканчиваются ({len(low_stock)}):</b>\n"
        for prod in low_stock[:5]:
            report += f"• {prod.get('name', 'Неизвестно')}: "
            report += f"{prod.get('quantity', 0)} шт.\n"
    
    out_of_stock = inventory.get('out_of_stock', [])
    if out_of_stock:
        report += f"\n❌ <b>Нет в наличии ({len(out_of_stock)}):</b>\n"
        for prod in out_of_stock[:5]:
            report += f"• {prod.get('name', 'Неизвестно')}\n"
    
    return report


def get_customer_details(user_id: int) -> Dict[str, Any]:
    """
    Получить детальную информацию о клиенте
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Dict с информацией о клиенте
    """
    with get_db_connection() as conn:
        # Основная информация
        cursor = conn.execute("""
            SELECT * FROM users WHERE user_id = ?
        """, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return {}
        
        # Заказы
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                COALESCE(SUM(total_amount), 0) as total_spent
            FROM orders
            WHERE user_id = ? AND status NOT IN ('cancelled')
        """, (user_id,))
        orders_stats = cursor.fetchone()
        
        # Последние заказы
        cursor = conn.execute("""
            SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (user_id,))
        recent_orders = cursor.fetchall()
        
        # Адреса
        cursor = conn.execute("""
            SELECT * FROM user_addresses
            WHERE user_id = ?
        """, (user_id,))
        addresses = cursor.fetchall()
        
    return {
        'user': dict(user) if user else {},
        'total_orders': orders_stats['total'] if orders_stats else 0,
        'total_spent': orders_stats['total_spent'] if orders_stats else 0,
        'recent_orders': [dict(o) for o in recent_orders],
        'addresses': [dict(a) for a in addresses]
    }


def format_customer_report(customer: Dict[str, Any]) -> str:
    """
    Сформировать текст отчета о клиенте
    """
    user = customer.get('user', {})
    
    report = "👤 <b>Информация о клиенте</b>\n\n"
    
    name = user.get('first_name') or user.get('username') or 'Аноним'
    report += f"• Имя: {name}\n"
    report += f"• ID: {user.get('user_id', 'Неизвестно')}\n"
    report += f"• Username: @{user.get('username', 'не указан')}\n"
    report += f"• Телефон: {user.get('phone', 'не указан')}\n"
    report += f"• В базе с: {user.get('created_at', 'неизвестно')}\n\n"
    
    report += "<b>📊 Статистика:</b>\n"
    report += f"• Всего заказов: {customer.get('total_orders', 0)}\n"
    report += f"• Всего потрачено: {customer.get('total_spent', 0):.0f} руб.\n"
    
    addresses = customer.get('addresses', [])
    if addresses:
        report += f"\n<b>📍 Адреса ({len(addresses)}):</b>\n"
        for addr in addresses[:3]:
            report += f"• {addr.get('address', 'Не указан')}\n"
    
    recent = customer.get('recent_orders', [])
    if recent:
        report += f"\n<b>📦 Последние заказы:</b>\n"
        for order in recent[:3]:
            report += f"• #{order.get('id', '?')}: "
            report += f"{order.get('total_amount', 0)} руб. "
            report += f"({order.get('status', 'unknown')})\n"
    
    return report
