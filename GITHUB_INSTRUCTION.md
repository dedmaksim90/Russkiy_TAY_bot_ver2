# 📤 Как загрузить бота в GitHub

## ⚡ Быстрая инструкция

### 1. Откройте PowerShell в папке бота

Нажмите `Win + R`, введите:
```
powershell
```

Затем в PowerShell:
```powershell
cd "c:\Users\User\Desktop\TG bot"
```

### 2. Инициализируйте Git

```powershell
git init
```

### 3. Добавьте все файлы

```powershell
git add .
```

### 4. Сделайте коммит

```powershell
git commit -m "Бот с SQLite и новыми категориями"
```

### 5. Создайте репозиторий на GitHub

1. Зайдите на https://github.com/new
2. Название: `tg-bot-shop`
3. Нажмите **Create repository**
4. Скопируйте URL (например: `https://github.com/username/tg-bot-shop.git`)

### 6. Привяжите репозиторий

```powershell
git remote add origin https://github.com/ВАШ_USERNAME/tg-bot-shop.git
```

### 7. Отправьте файлы

```powershell
git branch -M main
git push -u origin main
```

**Готово!** ✅ Файлы в GitHub

---

## 📁 Какие файлы загружаются

### ✅ Загружаются:
- `bot_test.py` - код бота
- `database.py` - база данных
- `analytics.py` - статистика
- `requirements.txt` - зависимости
- `.gitignore` - настройки игнора
- `*.md` - инструкции

### ❌ НЕ загружаются (в .gitignore):
- `shop.db` - файл базы (создается автоматически)
- `__pycache__/` - кэш Python
- `.env` - токены

---

## 🔄 Как обновлять код

После изменений в коде:

```powershell
git add .
git commit -m "Описание изменений"
git push
```

Bothost автоматически обновит бота!

---

## 🆘 Если есть ошибки

### "git is not recognized"
Установите Git: https://git-scm.com/ru/

### "remote origin already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/username/repo.git
```

### "permission denied"
Проверьте, что создали репозиторий и используете правильный URL

---

## 📊 Новые категории в боте

Теперь в категории **🍗 Мясо** есть:

### ❄️ Охлажденное / 🧊 Замороженное
- Цыпленок бройлер
- Молодой петушок
- Цесарка
- Перепелка

### 🥩 Частями (упаковками)
- Грудка (1 шт в упак)
- Окорочка (3 шт в упак)
- Крылья (8 шт в упак)
- Спинки (1 шт в упак)

### 🥣 Потроха
- Сердце (0.5 кг упак)
- Печень (0.5 кг упак)
- Шея (шт)

### 🥩 Фарш (шаг 100гр)
- Фарш 60/40 (грудка/бедро)
- Фарш 100% грудка

---

**Успешного деплоя!** 🚀
