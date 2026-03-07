# 📦 Подготовка файлов для GitHub и Bothost

## ✅ Файлы в папке "для запуска"

### Основные файлы (8 файлов):

| Файл | Зачем |
|------|-------|
| `bot_test.py` | Главный файл бота |
| `database.py` | Модуль базы данных SQLite |
| `analytics.py` | Модуль статистики |
| `requirements.txt` | Зависимости |
| `.gitignore` | Игнор файлов |
| `migrate_from_old_bot.py` | Скрипт миграции из старого бота |
| `migrate_to_sqlite.py` | Скрипт миграции в SQLite |
| `test_database.py` | Тесты базы данных |

---

## 🚀 Инструкция по подготовке

### Шаг 1: Скопируйте shop_data.json

**ВАЖНО:** Перед отправкой в GitHub нужно добавить `shop_data.json` из вашего старого бота!

```
1. Найдите shop_data.json из старого рабочего бота
2. Скопируйте в папку: c:\Users\User\Desktop\TG bot\для запуска\shop_data.json
```

### Шаг 2: Проверьте файлы

В папке должны быть:
```
✅ bot_test.py
✅ database.py
✅ analytics.py
✅ requirements.txt
✅ .gitignore
✅ migrate_from_old_bot.py
✅ shop_data.json  ← ВАЖНО!
```

### Шаг 3: Инициализируйте Git

Откройте PowerShell в папке "для запуска":
```powershell
cd "c:\Users\User\Desktop\TG bot\для запуска"
git init
```

### Шаг 4: Добавьте файлы

```powershell
git add .
```

### Шаг 5: Проверьте, что будет отправлено

```powershell
git status
```

**Убедитесь, что в списке НЕТ:**
- ❌ `shop.db` (база данных)
- ❌ `.env` (токены)
- ❌ `__pycache__/` (кэш)

### Шаг 6: Сделайте коммит

```powershell
git commit -m "Бот с SQLite базой данных - миграция из старого бота"
```

### Шаг 7: Создайте репозиторий на GitHub

1. Зайдите на https://github.com/new
2. Название: `tg-bot-shop` (или любое)
3. Сделайте Public или Private
4. Нажмите **Create repository**
5. Скопируйте URL репозитория

### Шаг 8: Отправьте в GitHub

```powershell
git remote add origin https://github.com/ВАШ_USERNAME/tg-bot-shop.git
git branch -M main
git push -u origin main
```

---

## 📊 Что будет в GitHub:

### ✅ Загружено:
- bot_test.py (код бота)
- database.py (база данных)
- analytics.py (статистика)
- requirements.txt (зависимости)
- .gitignore (настройки)
- migrate_from_old_bot.py (миграция)
- shop_data.json (старые данные)
- *.md (инструкции)

### ❌ НЕ загружено:
- shop.db (база данных - создается автоматически)
- .env (токены - опасно!)
- __pycache__/ (кэш)

---

## 🔄 На Bothost:

### 1. Подключите репозиторий:
- Панель Bothost → Создать проект
- Выбрать GitHub
- Выбрать репозиторий: `tg-bot-shop`

### 2. Добавьте переменные окружения:
```
BOT_TOKEN=ваш_токен_бота
OWNER_ID=439446887
```

### 3. Главный файл:
```
bot_test.py
```

### 4. Нажмите Deploy!

---

## ⚠️ Важно про базу данных:

### Проблема:
Bothost может сбрасывать `shop.db` при каждом деплое.

### Решение 1 (рекомендуется):
Использовать внешнюю базу данных (PostgreSQL):
1. Зарегистрируйтесь на https://elephantsql.com/
2. Создайте бесплатную базу
3. Получите URL подключения
4. Добавьте переменную на Bothost: `DATABASE_URL=postgresql://...`
5. Обновите `database.py` для использования PostgreSQL

### Решение 2:
Храните данные в JSON (старый формат):
1. Используйте `shop_data.json` для хранения данных
2. Бот будет читать/писать в JSON файл

---

## ✅ Проверка после деплоя:

1. Откройте бота в Telegram
2. Нажмите `/start`
3. Проверьте каталог (должны быть товары)
4. Проверьте заказы (должны быть старые заказы)

---

**Готово!** 🎉
