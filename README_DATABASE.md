# 🗄️ Локальная база данных SQLite для Telegram бота

## 📋 Описание

Бот теперь использует **SQLite** для хранения всех данных. Это обеспечивает:

- ✅ **Надежность** — транзакции, целостность данных
- ✅ **Производительность** — быстрый поиск и фильтрация
- ✅ **Масштабируемость** — работа с большими объемами данных
- ✅ **Статистику** — удобные SQL-запросы для аналитики
- ✅ **152-ФЗ** — автоматическое удаление персональных данных

## 📁 Структура базы данных

### Таблицы:

1. **users** — пользователи (клиенты и админы)
2. **user_addresses** — адреса доставки пользователей
3. **categories** — категории товаров
4. **products** — товары
5. **individual_products** — индивидуальные товары (тушки с точным весом)
6. **carts** — корзины покупателей
7. **orders** — заказы
8. **order_items** — элементы заказов
9. **notifications** — уведомления о появлении товара
10. **reviews** — отзывы о товарах
11. **product_views** — просмотры товаров
12. **returns** — возвраты
13. **statistics** — агрегированная статистика
14. **settings** — настройки бота

## 🚀 Установка и запуск

### 1. Миграция данных из JSON в SQLite

Если у вас есть данные в файле `shop_data.json`, выполните миграцию:

```bash
python migrate_to_sqlite.py
```

Скрипт:
- Создаст базу данных `shop.db`
- Инициализирует все таблицы
- Перенесет данные из JSON (если файл существует)
- Сохранит структуру категорий

### 2. Запуск бота

```bash
python bot_test.py
```

При запуске:
- Инициализируется база данных
- Загрузятся товары, заказы, отзывы
- Подключатся администраторы

## 📊 Модули

### database.py

Основной модуль работы с базой данных. Содержит функции:

**Пользователи:**
- `add_or_update_user()` — добавить/обновить пользователя
- `get_user()` — получить информацию о пользователе
- `is_admin()` — проверка статуса админа
- `get_all_customers()` — получить всех клиентов
- `update_user_stats()` — обновить статистику пользователя

**Товары:**
- `add_product()` — добавить товар
- `get_product()` — получить товар
- `get_all_products()` — получить все товары
- `update_product()` — обновить товар
- `delete_product()` — удалить товар
- `update_product_quantity()` — обновить остаток
- `get_low_stock_products()` — товары с низким остатком

**Заказы:**
- `create_order()` — создать заказ
- `add_order_item()` — добавить элемент заказа
- `get_order()` — получить заказ
- `get_user_orders()` — заказы пользователя
- `update_order_status()` — обновить статус заказа
- `get_orders_by_status()` — заказы по статусу

**Корзина:**
- `add_to_cart()` — добавить в корзину
- `get_cart()` — получить корзину
- `update_cart_item_quantity()` — обновить количество
- `remove_from_cart()` — удалить из корзины
- `clear_cart()` — очистить корзину

**Отзывы:**
- `add_review()` — добавить отзыв
- `get_product_reviews()` — получить отзывы
- `get_product_rating()` — средний рейтинг
- `approve_review()` — одобрить отзыв

**Статистика:**
- `get_sales_statistics()` — статистика продаж
- `get_top_products()` — топ товаров
- `get_top_customers()` — топ клиентов
- `save_daily_statistic()` — сохранить дневную статистику

### analytics.py

Модуль аналитики и отчетности. Содержит функции:

- `get_full_statistics()` — полная статистика за период
- `format_statistics_report()` — текстовый отчет по статистике
- `get_daily_report()` — ежедневный отчет
- `format_daily_report()` — текст ежедневного отчета
- `get_inventory_status()` — статус инвентаря
- `format_inventory_report()` — отчет по инвентарю
- `get_customer_details()` — информация о клиенте
- `format_customer_report()` — отчет о клиенте

## 📈 Использование аналитики

### Пример получения статистики:

```python
from analytics import get_full_statistics, format_statistics_report

# Получить статистику за 30 дней
stats = get_full_statistics(days=30)

# Сформировать отчет
report = format_statistics_report(stats)

# Отправить администратору
await bot.send_message(OWNER_ID, report, parse_mode="HTML")
```

### Пример ежедневного отчета:

```python
from analytics import get_daily_report, format_daily_report
from datetime import datetime

# Получить отчет за сегодня
daily = get_daily_report(datetime.now())

# Сформировать текст
report = format_daily_report(daily)

# Отправить
await bot.send_message(OWNER_ID, report, parse_mode="HTML")
```

## 🔄 Бэкап данных

### Экспорт в JSON:

```python
from database import export_to_json

# Создать бэкап
export_to_json('shop_data_backup.json')
```

### Импорт из JSON (миграция):

```python
from database import migrate_from_json

# Мигрировать данные
migrate_from_json('shop_data.json')
```

## 🔧 Настройки

### Параметры в database.py:

```python
DB_PATH = Path(__file__).parent / "shop.db"  # Путь к базе данных
```

### Автоматическое удаление старых данных (152-ФЗ):

```python
# В bot_test.py
await auto_delete_old_orders(days=30)  # Удалять заказы старше 30 дней
```

## 📝 Примеры SQL-запросов

### Получить выручку за месяц:

```sql
SELECT 
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue
FROM orders
WHERE status NOT IN ('cancelled')
AND created_at >= datetime('now', '-30 days')
```

### Топ товаров:

```sql
SELECT 
    p.name,
    SUM(oi.quantity) as total_sold,
    SUM(oi.total) as revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.id
JOIN orders o ON oi.order_id = o.id
WHERE o.status NOT IN ('cancelled')
GROUP BY p.id, p.name
ORDER BY total_sold DESC
LIMIT 10
```

### Активные клиенты:

```sql
SELECT 
    u.user_id,
    u.first_name,
    COUNT(o.id) as orders_count,
    SUM(o.total_amount) as total_spent
FROM users u
JOIN orders o ON u.user_id = o.user_id
WHERE o.status NOT IN ('cancelled')
AND o.created_at >= datetime('now', '-30 days')
GROUP BY u.user_id
ORDER BY total_spent DESC
```

## ⚠️ Важные замечания

1. **Не удаляйте файл `shop.db`** — это приведет к потере всех данных
2. **Регулярно делайте бэкапы** — используйте `export_to_json()`
3. **После миграции проверьте данные** — убедитесь, что все товары и заказы на месте
4. **Файл `shop_data.json` можно удалить** — после успешной миграции и проверки

## 🆘 Решение проблем

### Ошибка "database is locked":

```python
# Убедитесь, что все подключения закрыты
# Используйте контекстный менеджер get_db_connection()
```

### Ошибка миграции:

```bash
# Проверьте наличие JSON файла
ls shop_data.json

# Проверьте права доступа
chmod 644 shop_data.json
```

### Бот не видит данные:

```python
# Проверьте загрузку данных
from database import get_all_products
products = get_all_products()
print(f"Товаров в БД: {len(products)}")
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи бота
2. Проверьте целостность базы данных
3. Восстановите из бэкапа при необходимости

---

**Русский ТАЙ** — Семейная ферма 🏡
Версия: 2.0 (SQLite)
