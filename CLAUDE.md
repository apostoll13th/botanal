# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Telegram expense tracking bot built with python-telegram-bot. The bot helps users track expenses, manage budgets, set savings goals, and receive financial reminders. Currently, all code is in a single file (bot.py) which needs refactoring for deployment on Ubuntu server.

**NEW**: The project now includes a web interface for viewing statistics and analytics through a browser.

## Key Commands

### Running the Bot
```bash
# Set environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Run the bot
python bot.py
```

### Running with Docker Compose
```bash
# Full stack (database + bot + Go backend + frontend)
docker compose up --build

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Dependencies Installation (for local development)
```bash
# Bot dependencies
pip install -r requirements.txt

# Go backend dependencies
cd backend-go && go mod download

# Frontend - no dependencies (pure HTML/JS/CSS served by Nginx)
```

## Architecture Overview

### Project Structure
- **bot.py**: Main Telegram bot (refactored into modules)
- **handlers.py**: Bot command and conversation handlers
- **database.py**: Database operations
- **utils.py**: Helper functions and chart generation
- **config.py**: Configuration management
- **db.py, db_schema.py, database_migrations.py**: Database layer
- **backend-go/**: Go REST API + schema owner
  - main.go: API server with Gin framework
  - schema.go: Database bootstrap + migrations
  - go.mod: Go dependencies
- **backend/**: Legacy Flask API (deprecated, use Go version)
- **frontend-react/**: React 18 UI (PWA)
  - src/components: Overview/Expenses/Budgets/Goals
  - src/services/api.js: Axios client (`/api/*`)
  - nginx.conf: Nginx configuration for production build

### Current Bot Structure (Refactored)
- **bot.py**: Main entry point and orchestration (161 lines)
- **handlers.py**: All command and conversation handlers
- **database.py**: Database operations layer
- **utils.py**: Helper functions and chart generation with matplotlib
- **config.py**: Centralized configuration management
- **db.py, db_schema.py**: Database connection and schema
- **database_migrations.py**: Proper migration system

### Database Schema
- **users**: Telegram profiles (`user_id`, `user_name`, `created_date`)
- **app_users**: Логин/пароль/роль для входа в UI + связь с конкретным `user_id`
- **expenses**: Все операции с колонкой `transaction_type` (`expense`/`income`)
- **budgets**: Budget limits by category/period
- **savings_goals**: Financial targets
- **reminders**: Scheduled reminders
- **categories**: Master list of categories with type (`expense`/`income`)
- **migrations**: История миграций из Go backend (`schema.go`)

> Schema & migrations живут в `backend-go/schema.go`. Bot больше не выполняет DDL, а аутентификация реализована через таблицу `app_users` + HMAC-токены.

### Core Features
1. **Expense Management**: Add expenses with categories, view reports
2. **Budget Tracking**: Set budgets by category (daily/weekly/monthly)
3. **Savings Goals**: Create and track progress
4. **Reports**: Generate daily/weekly/monthly reports with charts
5. **Reminders**: Set recurring reminders
6. **Multi-user**: Supports multiple users with username tracking
7. **PWA UI**: Добавление расходов/доходов и управление категориями через React UI

### Conversation Flows
- EXPENSE_ENTRY: Multi-step expense addition
- BUDGET_SETTING: Category and amount selection
- GOAL_CREATION: Savings goal setup
- REMINDER_CREATION: Reminder configuration

## ✅ Completed Refactoring

### What's Been Done
1. ✅ **Created requirements.txt** with proper versions
2. ✅ **Split bot.py** into modules:
   - handlers.py: Command and conversation handlers
   - database.py: Database operations
   - utils.py: Helper functions and chart generation
   - config.py: Configuration management
3. ✅ **Added .env.example** file for configuration
4. ✅ **Implemented proper database migrations** system
5. ✅ **Added logging** throughout all modules
6. ✅ **Created Docker infrastructure** for deployment
7. ✅ **Added error handling** in database and API layers
8. ✅ **Created Go backend** for REST API (Gin framework)
9. ✅ **Created React frontend** for web interface
10. ✅ **Перенесли создание/миграции схемы в Go backend + добавили REST CRUD для UI (категории, операции, пользователи)**

### Database Migration Notes
- Все миграции описываются в `backend-go/schema.go` (структура `migration`).
- Любое изменение схемы → новый `version` + `up`-функция.
- Backend применяет миграции автоматически при старте, поэтому не нужно держать дубли в Python.

## Deployment Considerations

### Ubuntu Server Setup
1. Ensure Python 3.8+ is installed
2. Set up virtual environment
3. Configure systemd service for auto-restart
4. Set up logging to file
5. Consider using supervisor or systemd for process management
6. Set up proper file permissions for database

### Security Considerations
- Bot token must be in environment variable, never hardcoded
- Database file permissions should be restricted
- Веб-доступ защищён логином/паролем (`app_users` + токен в заголовке Authorization)
- Implement rate limiting for expensive operations (chart generation)

## Common Development Tasks

### Adding New Command
1. Add handler in main() function
2. Create handler function following existing pattern
3. Add to help message in help_command()

### Adding Database Column
1. Добавить колонку/таблицу в `createBaseTables()` или новую миграцию в `runMigrations()` (`backend-go/schema.go`).
2. Обновить Go-структуры и SQL (`backend-go/main.go`) + фронтенд API/компоненты, если поле нужно UI.
3. При необходимости обновить Python-бот (`database.py`) только для бизнес-логики (без DDL).

### Testing
Currently no tests exist. When adding tests:
- Mock telegram.Update and telegram.ext.CallbackContext
- Test database operations separately
- Test chart generation with sample data

## Known Issues
1. Legacy references to монолитного бота/старого `user_id`-флоу ещё встречаются в некоторых документах.
2. Нет пагинации/поиска в новом списке операций (может быть тяжелым при большом объеме).
3. Смешанный RU/EN UI и комментарии.
4. Валидация сумм/дат на фронте минимальна.
5. Chart generation can be slow for large datasets.

## REST API Cheatsheet

| Method | Endpoint | Описание |
|--------|----------|----------|
| `POST` | `/api/auth/login` | Получить токен по логину/паролю (`app_users`). |
| `GET`  | `/api/me` | Данные авторизованного пользователя (роль, login, telegram_user_id). |
| `GET`  | `/api/expenses` | Список операций (query `start_date`, `end_date`, `category`, `type`). |
| `POST` | `/api/expenses` | Создание расхода или дохода (`transaction_type`). |
| `GET`  | `/api/budgets` | Бюджеты текущего пользователя. |
| `GET`  | `/api/goals` | Цели экономии. |
| `GET`  | `/api/categories` | Получить справочник категорий. |
| `POST` | `/api/categories` | Создать/обновить категорию. |

Backend автоматически приводит схему в порядок при старте (см. `schema.go`), поэтому при любых изменениях БД достаточно перезапустить сервис `backend`. Токены подписываются HMAC (секрет `AUTH_SECRET`), UI хранит их в `localStorage` и отправляет в `Authorization: Bearer ...`.
