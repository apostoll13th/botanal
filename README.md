# 💰 Telegram Expense Tracker Bot

Современный бот для учета личных финансов с веб-интерфейсом.

## 🚀 Технологический стек

### Backend
- **Telegram Bot**: Python 3.11 + python-telegram-bot
- **REST API**: Go 1.21 + Gin framework
- **Database**: PostgreSQL 15

### Frontend
- **React** 18.2 + Hooks
- **Chart.js** 4.4 для графиков
- **Axios** для API запросов
- **Nginx** для production

### Infrastructure
- **Docker** + **Docker Compose** для оркестрации
- Multi-stage builds для оптимизации образов

## ✨ Возможности

### Через Telegram бота
- ➕ Добавление расходов с категориями
- 📊 Ежедневные/еженедельные/месячные отчеты
- 💰 Установка бюджетов по категориям
- 🎯 Цели экономии
- 🔔 Напоминания
- 👥 Мультиюзер поддержка

### Через веб-интерфейс
- 📈 Интерактивные графики расходов
- 🥧 Круговая диаграмма по категориям
- 📉 График динамики расходов по дням
- 📋 Таблица всех операций с фильтрацией
- 💳 Отслеживание бюджетов с прогресс-барами
- 🎯 Визуализация прогресса по целям

## 🏃 Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Telegram Bot Token от [@BotFather](https://t.me/botfather)

### Запуск

1. **Клонируйте репозиторий**
```bash
git clone <your-repo-url>
cd telega_bot
```

2. **Создайте .env файл**
```bash
cp .env.example .env
```

3. **Настройте переменные окружения**

Отредактируйте `.env` и укажите ваш Telegram Bot Token:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://postgres:postgres@db:5432/expenses
WEB_APP_URL=http://localhost:8080
```

4. **Запустите все сервисы**
```bash
docker compose up --build
```

Это запустит:
- 🐘 PostgreSQL на порту 5432
- 🤖 Telegram Bot
- 🔷 Go API на порту 5000
- ⚛️ React App на порту 8080

5. **Откройте веб-интерфейс**
```
http://localhost:8080?user_id=YOUR_TELEGRAM_USER_ID
```

## 📁 Структура проекта

```
.
├── backend-go/              # Go REST API
│   ├── main.go             # Gin сервер
│   ├── go.mod
│   └── go.sum
│
├── frontend-react/          # React приложение
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   │   ├── Overview.js
│   │   │   ├── Expenses.js
│   │   │   ├── Budgets.js
│   │   │   └── Goals.js
│   │   ├── services/
│   │   │   └── api.js      # API клиент
│   │   ├── App.js
│   │   └── index.js
│   ├── nginx.conf          # Nginx конфигурация
│   └── package.json
│
├── bot.py                   # Telegram bot (refactored)
├── handlers.py              # Bot handlers
├── database.py              # Database operations
├── utils.py                 # Utilities
├── config.py                # Configuration
│
├── docker-compose.yml       # Оркестрация сервисов
├── Dockerfile.bot           # Dockerfile для бота
├── Dockerfile.backend-go    # Dockerfile для Go API
├── Dockerfile.frontend-react # Dockerfile для React
│
├── .env.example             # Пример конфигурации
├── requirements.txt         # Python зависимости
└── README.md                # Этот файл
```

## 🔧 Разработка

### Запуск backend отдельно (Go)

```bash
cd backend-go
go mod download
go run main.go
```

### Запуск frontend отдельно (React)

```bash
cd frontend-react
npm install
npm start
```

Откроется на http://localhost:3000

### Запуск бота отдельно (Python)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_token"
python bot.py
```

## 🐳 Docker команды

```bash
# Запуск всех сервисов
docker compose up -d

# Просмотр логов
docker compose logs -f

# Просмотр логов конкретного сервиса
docker compose logs -f bot
docker compose logs -f backend
docker compose logs -f frontend

# Остановка всех сервисов
docker compose down

# Пересборка после изменений
docker compose up --build

# Очистка volumes (УДАЛИТ базу данных!)
docker compose down -v
```

## 📊 API Endpoints

Backend предоставляет следующие REST API эндпоинты:

- `GET /api/health` - Проверка работоспособности
- `GET /api/user/:user_id` - Информация о пользователе
- `GET /api/expenses/:user_id` - Расходы (с фильтрами)
- `GET /api/expenses-summary/:user_id` - Сводка за 30 дней
- `GET /api/budgets/:user_id` - Бюджеты пользователя
- `GET /api/goals/:user_id` - Цели экономии

### Примеры запросов

```bash
# Получить расходы за период
curl "http://localhost:5000/api/expenses/123456?start_date=2024-01-01&end_date=2024-12-31"

# Получить сводку
curl "http://localhost:5000/api/expenses-summary/123456"

# Проверить здоровье API
curl "http://localhost:5000/api/health"
```

## 🗄️ База данных

### Схема

- **users** - пользователи бота
- **expenses** - расходы
- **budgets** - бюджеты по категориям
- **savings_goals** - цели экономии
- **reminders** - напоминания
- **migrations** - история миграций

### Бэкап и восстановление

```bash
# Создать бэкап
docker compose exec db pg_dump -U postgres expenses > backup.sql

# Восстановить из бэкапа
docker compose exec -T db psql -U postgres expenses < backup.sql
```

## 🔐 Безопасность

- ✅ Секреты в `.env` файле (не коммитятся в Git)
- ✅ PostgreSQL изолирован в Docker сети
- ✅ CORS настроен для frontend
- ✅ Minimal Docker images (Alpine Linux)
- ✅ Multi-stage builds для уменьшения размера образов

## 🌐 Деплой на production

См. подробное руководство в [DEPLOYMENT.md](DEPLOYMENT.md)

Основные шаги:
1. Настройте Ubuntu сервер с Docker
2. Клонируйте проект
3. Настройте `.env` с production параметрами
4. Запустите `docker compose up -d`
5. Настройте reverse proxy (Nginx) с SSL

## 🤝 Contributing

1. Fork проект
2. Создайте feature ветку (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 License

MIT License - см. файл [LICENSE](LICENSE)

## 📧 Контакты

Для вопросов и предложений создавайте Issue в репозитории.

---

**Сделано с ❤️ и React + Go**
