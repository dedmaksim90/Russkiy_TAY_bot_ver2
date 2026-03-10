# 🚀 Деплой бота с SQLite на Bothost через GitHub

## ⚠️ Важное предупреждение

**SQLite на хостингах имеет ограничения:**
- Файл базы данных может **сбрасываться** при каждом деплое
- Некоторые хостинги имеют **read-only файловую систему**
- При перезапуске бота данные могут **теряться**

## 📋 Проверка Bothost

Перед деплоем проверьте:

1. **Поддерживает ли Bothost запись на диск?**
   - Зайдите в панель управления Bothost
   - Проверьте документацию
   - Попробуйте создать файл через консоль

2. **Есть ли постоянное хранилище?**
   - Некоторые тарифы предоставляют `/data` или `/persistent` директорию
   - Узнайте путь к постоянному хранилищу

---

## 🔄 Вариант 1: Bothost поддерживает запись на диск

### Шаг 1: Подготовка репозитория GitHub

1. **Создайте репозиторий на GitHub:**
   ```bash
   # В папке с ботом
   git init
   git add .
   git commit -m "Бот с SQLite базой данных"
   ```

2. **Добавьте удаленный репозиторий:**
   ```bash
   git remote add origin https://github.com/ВАШ_USERNAME/ВАШ_REPO.git
   git push -u origin main
   ```

3. **Проверьте .gitignore:**
   - Файл `shop.db` НЕ должен загружаться в Git
   - Все остальные файлы загружаются

### Шаг 2: Настройка Bothost

1. **В панели Bothost:**
   - Привяжите репозиторий GitHub
   - Укажите путь к основному файлу: `bot_test.py`
   - Добавьте переменные окружения:
     ```
     BOT_TOKEN=ваш_токен
     OWNER_ID=ваш_id
     ```

2. **Настройка базы данных:**
   - В файле `database.py` измените путь к БД:
   ```python
   # Для Bothost
   DB_PATH = Path(__file__).parent / "shop.db"
   # Или используйте абсолютный путь к постоянному хранилищу
   # DB_PATH = Path("/data/shop.db")  # если есть /data
   ```

### Шаг 3: Первый запуск

1. **Задеплойте бота:**
   ```bash
   git push origin main
   ```

2. **Bothost автоматически:**
   - Скачает файлы из GitHub
   - Установит зависимости
   - Запустит `bot_test.py`

3. **База данных создастся автоматически** при первом запуске

### Шаг 4: Миграция данных (если нужно)

Если у вас есть данные в `shop_data.json`:

1. **Загрузите JSON на Bothost:**
   - Через FTP/SFTP
   - Или через консоль Bothost

2. **Запустите миграцию:**
   - В панели Bothost выполните:
   ```bash
   python migrate_to_sqlite.py
   ```

3. **Перезапустите бота**

---

## 🔄 Вариант 2: Bothost НЕ поддерживает запись (рекомендуется)

Используйте **внешнюю базу данных**:

### PostgreSQL (рекомендуется)

1. **Создайте PostgreSQL базу:**
   - На [ElephantSQL](https://www.elephantsql.com/) (бесплатно)
   - Или на [Railway](https://railway.app/)
   - Или на [Supabase](https://supabase.com/)

2. **Получите connection string:**
   ```
   postgresql://user:password@host:port/database
   ```

3. **Обновите `database.py`:**

```python
# Вместо SQLite используйте PostgreSQL
import psycopg2  # добавьте в requirements.txt

def get_db_connection():
    conn = psycopg2.connect(
        os.getenv('DATABASE_URL')
    )
    return conn
```

4. **Добавьте переменную окружения на Bothost:**
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

5. **Задеплойте:**
   ```bash
   git push origin main
   ```

### MongoDB (альтернатива)

1. **Создайте MongoDB Atlas:**
   - [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (бесплатно 512MB)

2. **Используйте pymongo:**
   ```python
   from pymongo import MongoClient
   
   client = MongoClient(os.getenv('MONGODB_URI'))
   db = client['shop_bot']
   ```

---

## 🔄 Вариант 3: Гибридный (SQLite + синхронизация)

### Локальная разработка с SQLite

1. **Разрабатывайте локально:**
   ```bash
   python bot_test.py
   ```

2. **Данные хранятся в `shop.db`**

### На Bothost используйте JSON

1. **Обновите `bot_test.py` для Bothost:**

```python
# В начале файла
import os

ON_BOTHOST = os.getenv('BOTHOST', 'false') == 'true'

if ON_BOTHOST:
    # Использовать JSON вместо SQLite
    DATA_FILE = 'shop_data.json'
else:
    # Использовать SQLite локально
    import database as db
```

2. **Настройте `.gitignore`:**
   ```
   shop.db
   *.pyc
   __pycache__/
   ```

3. **Задеплойте:**
   ```bash
   git push origin main
   ```

---

## 📝 Пошаговая инструкция для GitHub → Bothost

### 1. Подготовка файлов

```bash
# В папке с ботом
cd "c:\Users\User\Desktop\TG bot"

# Инициализация Git
git init

# Проверка .gitignore
# Убедитесь, что shop.db в .gitignore

# Добавление файлов
git add .
git commit -m "Initial commit with SQLite database"
```

### 2. Создание репозитория

1. Зайдите на [GitHub](https://github.com/)
2. Создайте новый репозиторий: `tg-bot-shop`
3. Скопируйте URL репозитория

### 3. Отправка в GitHub

```bash
git remote add origin https://github.com/ВАШ_USERNAME/tg-bot-shop.git
git branch -M main
git push -u origin main
```

### 4. Настройка Bothost

1. **Войдите в панель Bothost**
2. **Создайте новый проект:**
   - Название: `Russian TAY Bot`
   - Тип: Python

3. **Подключите GitHub:**
   - Выберите репозиторий: `tg-bot-shop`
   - Ветка: `main`

4. **Настройте переменные окружения:**
   ```
   BOT_TOKEN=1234567890:AAF...
   OWNER_ID=439446887
   BOTHOST=true
   ```

5. **Укажите главный файл:**
   ```
   bot_test.py
   ```

6. **Нажмите "Deploy"**

### 5. Проверка

1. **Bothost начнет деплой:**
   - Скачает файлы из GitHub
   - Установит `aiogram`
   - Запустит бота

2. **Проверьте логи:**
   - В панели Bothost откройте логи
   - Убедитесь, что бот запустился

3. **Проверьте бота:**
   - Откройте Telegram
   - Нажмите `/start`

---

## 🔧 Решение проблем

### Ошибка: "database is locked"

**Проблема:** SQLite не работает на read-only хостинге

**Решение:**
```python
# Используйте PostgreSQL вместо SQLite
# См. Вариант 2 выше
```

### Ошибка: "Cannot write to file"

**Проблема:** Нет прав на запись

**Решение:**
1. Узнайте путь к постоянному хранилищу
2. Обновите `DB_PATH` в `database.py`:
   ```python
   DB_PATH = Path("/data/shop.db")  # или другой путь
   ```

### Бот перезапускается и данные теряются

**Проблема:** Файл БД сбрасывается при деплое

**Решение:**
1. Используйте внешнюю БД (PostgreSQL/MongoDB)
2. Или храните данные в JSON и загружайте в Git (для небольших объемов)

---

## 📊 Рекомендуемая архитектура для продакшена

```
┌─────────────┐
│   GitHub    │ ← Хранит код (без shop.db)
└──────┬──────┘
       │
       ↓ деплой
┌─────────────┐
│   Bothost   │ ← Запускает бота
└──────┬──────┘
       │
       ↓ подключение
┌─────────────┐
│  PostgreSQL │ ← Хранит данные (внешний сервис)
│  (ElephantSQL)│
└─────────────┘
```

---

## ✅ Чеклист перед деплоем

- [ ] Все файлы в `.gitignore` (shop.db, __pycache__, .env)
- [ ] Токен бота в переменных окружениях (НЕ в коде!)
- [ ] OWNER_ID настроен
- [ ] `requirements.txt` содержит все зависимости
- [ ] Протестирована локальная работа
- [ ] Создан репозиторий на GitHub
- [ ] Bothost подключен к GitHub
- [ ] Переменные окружения настроены на Bothost

---

## 📞 Если что-то пошло не так

1. **Проверьте логи на Bothost**
2. **Проверьте переменные окружения**
3. **Убедитесь, что база данных создается**
4. **Попробуйте простой тест:**
   ```python
   # Временно добавьте в bot_test.py
   @dp.message_handler(commands=['test'])
   async def test_db(message: types.Message):
       from database import get_all_products
       products = get_all_products()
       await message.answer(f"Товаров в БД: {len(products)}")
   ```

---

**Удачи с деплоем!** 🚀

Если Bothost не поддерживает SQLite, используйте **PostgreSQL на ElephantSQL** - это бесплатно и надежно.
