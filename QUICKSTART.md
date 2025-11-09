# ⚡ Quick Start Guide

## Минимальная инструкция для запуска за 5 минут

### Требования
- Docker и Docker Compose
- Telegram Bot Token

### Шаги

1. **Клонировать проект**
```bash
git clone <your-repo>
cd telega_bot
```

2. **Создать .env**
```bash
cp .env.example .env
```

3. **Добавить токен**

Откройте `.env` и вставьте ваш Telegram Bot Token:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

4. **Запустить**
```bash
docker compose up --build
```

Подождите 1-2 минуты пока соберутся образы.

5. **Готово!**

✅ Бот работает - попробуйте команду `/start` в Telegram

✅ Веб-интерфейс: http://localhost:8080?user_id=YOUR_TELEGRAM_ID

✅ API: http://localhost:5000/api/health

## Как узнать свой Telegram User ID?

1. Напишите боту `/start`
2. Или используйте бот [@userinfobot](https://t.me/userinfobot)

## Проблемы?

### Порты заняты
```bash
# Измените порты в docker-compose.yml
ports:
  - "8081:80"  # вместо 8080
  - "5001:5000"  # вместо 5000
```

### База не запускается
```bash
# Очистите volumes
docker compose down -v
docker compose up --build
```

### Логи
```bash
# Смотреть логи
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f bot
docker compose logs -f backend
docker compose logs -f frontend
```

## Стек
- 🐍 Python Bot (refactored)
- 🔷 Go API
- ⚛️ React Frontend
- 🐘 PostgreSQL

**Полная документация:** см. [README.md](README.md)
