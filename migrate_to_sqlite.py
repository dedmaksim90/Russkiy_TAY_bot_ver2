"""
Скрипт миграции данных из JSON в SQLite
Запустить один раз для переноса всех данных
"""

import sys
import logging
from pathlib import Path

# Добавляем путь к боту
sys.path.insert(0, str(Path(__file__).parent))

from database import init_database, migrate_from_json, init_categories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 50)
    logger.info("🚀 Начало миграции данных в SQLite")
    logger.info("=" * 50)
    
    # Инициализация БД
    logger.info("1️⃣ Инициализация базы данных...")
    init_database()
    
    # Инициализация категорий
    logger.info("2️⃣ Инициализация категорий...")
    try:
        init_categories()
        logger.info("✅ Категории созданы")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при создании категорий: {e}")
    
    # Миграция данных
    logger.info("3️⃣ Миграция данных из JSON...")
    success = migrate_from_json('shop_data.json')
    
    if success:
        logger.info("=" * 50)
        logger.info("✅ Миграция успешно завершена!")
        logger.info("📄 Данные теперь хранятся в shop.db")
        logger.info("💡 Можно удалить shop_data.json после проверки")
        logger.info("=" * 50)
    else:
        logger.warning("⚠️ Миграция не выполнена (возможно, нет JSON файла)")
        logger.info("💡 База данных пуста и готова к работе")
    
    logger.info("\n📊 Следующие шаги:")
    logger.info("   1. Проверить работу бота с новой БД")
    logger.info("   2. Убедиться, что все данные на месте")
    logger.info("   3. Удалить shop_data.json (опционально)")
    logger.info("   4. Обновить bot_test.py для работы с database.py")


if __name__ == '__main__':
    main()
