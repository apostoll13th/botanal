# Промт для Claude Code: Разработка платформы семейного бюджета

## Контекст проекта
Необходимо создать современную платформу для анализа семейных финансов с нуля. У нас уже есть Telegram-бот (код в репозитории), но нужно построить полноценную веб-платформу с отдельным backend на Go и frontend на React с PWA.

## Целевая архитектура

### Backend (Go)
- REST API на Go (использовать Gin или Echo framework)
- PostgreSQL как основная БД
- Миграции через golang-migrate или подобное
- JWT авторизация
- Swagger документация для API
- Docker-контейнер для деплоя

### Frontend (React + PWA)
- React 18+ с TypeScript
- Vite или Create React App
- Material-UI или Ant Design для UI компонентов
- Chart.js или Recharts для графиков
- PWA манифест для установки на мобильные устройства
- Service Worker для оффлайн режима
- Адаптивный дизайн (mobile-first)

### База данных (PostgreSQL)
Создать следующие таблицы через миграции:

**users** - пользователи системы
- id (PRIMARY KEY, SERIAL)
- email (UNIQUE, NOT NULL)
- password_hash (NOT NULL)
- full_name (TEXT)
- telegram_user_id (BIGINT, NULLABLE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

**families** - семейные группы
- id (PRIMARY KEY, SERIAL)
- name (TEXT, NOT NULL)
- created_by (FOREIGN KEY -> users.id)
- created_at (TIMESTAMP)

**family_members** - связь пользователей и семей
- id (PRIMARY KEY, SERIAL)
- family_id (FOREIGN KEY -> families.id)
- user_id (FOREIGN KEY -> users.id)
- role (ENUM: 'admin', 'member', 'viewer')
- joined_at (TIMESTAMP)

**categories** - категории расходов/доходов
- id (PRIMARY KEY, SERIAL)
- family_id (FOREIGN KEY -> families.id, NULLABLE для глобальных)
- name (TEXT, NOT NULL)
- type (ENUM: 'expense', 'income')
- icon (TEXT, NULLABLE)
- color (TEXT, NULLABLE)
- parent_category_id (FOREIGN KEY -> categories.id, NULLABLE для подкатегорий)
- is_active (BOOLEAN, DEFAULT TRUE)
- created_at (TIMESTAMP)

**transactions** - транзакции (расходы/доходы)
- id (PRIMARY KEY, SERIAL)
- family_id (FOREIGN KEY -> families.id)
- user_id (FOREIGN KEY -> users.id)
- category_id (FOREIGN KEY -> categories.id)
- amount (NUMERIC(12,2), NOT NULL)
- type (ENUM: 'expense', 'income')
- description (TEXT, NULLABLE)
- date (DATE, NOT NULL)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

**budgets** - бюджеты по категориям
- id (PRIMARY KEY, SERIAL)
- family_id (FOREIGN KEY -> families.id)
- category_id (FOREIGN KEY -> categories.id)
- amount (NUMERIC(12,2), NOT NULL)
- period (ENUM: 'daily', 'weekly', 'monthly', 'yearly')
- start_date (DATE)
- end_date (DATE, NULLABLE)
- is_active (BOOLEAN, DEFAULT TRUE)
- created_at (TIMESTAMP)

**savings_goals** - цели накоплений
- id (PRIMARY KEY, SERIAL)
- family_id (FOREIGN KEY -> families.id)
- name (TEXT, NOT NULL)
- description (TEXT, NULLABLE)
- target_amount (NUMERIC(12,2), NOT NULL)
- current_amount (NUMERIC(12,2), DEFAULT 0)
- target_date (DATE, NULLABLE)
- is_completed (BOOLEAN, DEFAULT FALSE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

**recurring_transactions** - регулярные платежи
- id (PRIMARY KEY, SERIAL)
- family_id (FOREIGN KEY -> families.id)
- category_id (FOREIGN KEY -> categories.id)
- amount (NUMERIC(12,2), NOT NULL)
- type (ENUM: 'expense', 'income')
- description (TEXT)
- frequency (ENUM: 'daily', 'weekly', 'monthly', 'yearly')
- start_date (DATE, NOT NULL)
- end_date (DATE, NULLABLE)
- next_execution_date (DATE)
- is_active (BOOLEAN, DEFAULT TRUE)
- created_at (TIMESTAMP)

## API Endpoints (Go Backend)

### Аутентификация
- `POST /api/v1/auth/register` - регистрация нового пользователя
- `POST /api/v1/auth/login` - авторизация (получение JWT токена)
- `POST /api/v1/auth/refresh` - обновление токена
- `POST /api/v1/auth/logout` - выход из системы
- `GET /api/v1/auth/me` - получить текущего пользователя

### Пользователи
- `GET /api/v1/users/profile` - профиль текущего пользователя
- `PUT /api/v1/users/profile` - обновить профиль
- `PUT /api/v1/users/password` - изменить пароль

### Семьи
- `POST /api/v1/families` - создать семью
- `GET /api/v1/families` - список семей пользователя
- `GET /api/v1/families/:id` - детали семьи
- `PUT /api/v1/families/:id` - обновить семью
- `DELETE /api/v1/families/:id` - удалить семью
- `POST /api/v1/families/:id/members` - добавить участника
- `DELETE /api/v1/families/:id/members/:userId` - удалить участника
- `PUT /api/v1/families/:id/members/:userId/role` - изменить роль участника

### Категории
- `POST /api/v1/categories` - создать категорию
- `GET /api/v1/categories` - список категорий (фильтр по family_id)
- `GET /api/v1/categories/:id` - детали категории
- `PUT /api/v1/categories/:id` - обновить категорию
- `DELETE /api/v1/categories/:id` - удалить категорию
- `GET /api/v1/categories/default` - список глобальных категорий

### Транзакции
- `POST /api/v1/transactions` - создать транзакцию
- `GET /api/v1/transactions` - список транзакций (фильтры: date_from, date_to, category_id, type, user_id)
- `GET /api/v1/transactions/:id` - детали транзакции
- `PUT /api/v1/transactions/:id` - обновить транзакцию
- `DELETE /api/v1/transactions/:id` - удалить транзакцию
- `POST /api/v1/transactions/bulk` - массовый импорт транзакций

### Бюджеты
- `POST /api/v1/budgets` - создать бюджет
- `GET /api/v1/budgets` - список бюджетов семьи
- `GET /api/v1/budgets/:id` - детали бюджета
- `PUT /api/v1/budgets/:id` - обновить бюджет
- `DELETE /api/v1/budgets/:id` - удалить бюджет
- `GET /api/v1/budgets/:id/status` - статус выполнения бюджета (потрачено/осталось/процент)

### Цели накоплений
- `POST /api/v1/goals` - создать цель
- `GET /api/v1/goals` - список целей семьи
- `GET /api/v1/goals/:id` - детали цели
- `PUT /api/v1/goals/:id` - обновить цель
- `DELETE /api/v1/goals/:id` - удалить цель
- `POST /api/v1/goals/:id/deposit` - добавить средства к цели

### Регулярные платежи
- `POST /api/v1/recurring` - создать регулярный платеж
- `GET /api/v1/recurring` - список регулярных платежей
- `GET /api/v1/recurring/:id` - детали регулярного платежа
- `PUT /api/v1/recurring/:id` - обновить регулярный платеж
- `DELETE /api/v1/recurring/:id` - удалить регулярный платеж

### Аналитика и отчеты
- `GET /api/v1/analytics/summary` - общая сводка (параметры: family_id, date_from, date_to)
  - Общие расходы/доходы
  - Баланс
  - Топ категорий
- `GET /api/v1/analytics/trends` - тренды расходов/доходов
  - По дням/неделям/месяцам
- `GET /api/v1/analytics/categories` - анализ по категориям
  - Распределение по категориям (для pie chart)
  - Сравнение с прошлым периодом
- `GET /api/v1/analytics/users` - анализ по пользователям семьи
- `GET /api/v1/analytics/budgets-overview` - общий обзор бюджетов
- `GET /api/v1/analytics/forecast` - прогноз расходов на основе истории
- `GET /api/v1/analytics/export` - экспорт данных (CSV, Excel)

### Дополнительные фичи
- `GET /api/v1/notifications` - уведомления пользователя
- `PUT /api/v1/notifications/:id/read` - пометить уведомление прочитанным
- `GET /api/v1/dashboard` - данные для главного дашборда

## Структура проекта

```
family-budget-platform/
├── backend/                    # Go backend
│   ├── cmd/
│   │   └── api/
│   │       └── main.go        # Entry point
│   ├── internal/
│   │   ├── api/               # HTTP handlers
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic
│   │   ├── repository/        # Database layer
│   │   ├── middleware/        # JWT auth, CORS, etc
│   │   └── config/            # Configuration
│   ├── migrations/            # SQL migrations
│   ├── pkg/                   # Shared packages
│   ├── go.mod
│   ├── go.sum
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/                  # React frontend
│   ├── public/
│   │   ├── manifest.json     # PWA manifest
│   │   ├── sw.js             # Service Worker
│   │   └── icons/            # PWA icons
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API calls
│   │   ├── hooks/            # Custom hooks
│   │   ├── context/          # React context
│   │   ├── utils/            # Helper functions
│   │   ├── assets/           # Images, styles
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
└── docker-compose.yml         # Orchestration для всего стека
```

## Задачи для Claude Code

### Фаза 1: Backend Setup
1. Создать структуру Go проекта с Gin/Echo
2. Настроить подключение к PostgreSQL
3. Создать все миграции для таблиц БД
4. Реализовать модели данных (structs)
5. Настроить JWT аутентификацию
6. Создать middleware (auth, CORS, logging)

### Фаза 2: Backend API
1. Реализовать все endpoints для аутентификации
2. Реализовать CRUD для всех сущностей (users, families, categories, transactions, budgets, goals)
3. Реализовать endpoints аналитики с агрегацией данных
4. Добавить валидацию запросов
5. Настроить Swagger документацию
6. Написать Dockerfile для backend

### Фаза 3: Frontend Setup
1. Создать React проект с TypeScript и Vite
2. Настроить роутинг (React Router)
3. Настроить состояние (Context API или Redux)
4. Создать сервисный слой для API calls (axios)
5. Настроить PWA (manifest.json, service worker)
6. Добавить UI библиотеку (Material-UI)

### Фаза 4: Frontend Pages
1. Страница авторизации/регистрации
2. Главный дашборд с общей аналитикой
3. Страница транзакций (список, добавление, редактирование)
4. Страница категорий
5. Страница бюджетов с прогресс-барами
6. Страница целей накоплений
7. Страница аналитики с графиками
8. Страница настроек профиля и семьи
9. Страница регулярных платежей

### Фаза 5: Визуализация
1. Круговая диаграмма распределения расходов
2. Линейные графики трендов
3. Прогресс-бары для бюджетов и целей
4. Сравнительные bar charts
5. Календарь с метками транзакций

### Фаза 6: Deployment
1. Docker Compose для всего стека (Postgres + Backend + Frontend)
2. Nginx конфигурация для фронтенда
3. Environment variables управление
4. README с инструкциями по запуску

## Технические требования

### Backend (Go)
- Go 1.21+
- Gin или Echo framework
- PostgreSQL driver (pgx)
- golang-migrate для миграций
- JWT-go для токенов
- validator для валидации
- godotenv для env переменных
- swagger для документации

### Frontend (React)
- React 18+ с TypeScript
- Vite для сборки
- React Router v6 для роутинга
- Axios для HTTP запросов
- Material-UI или Ant Design
- Chart.js или Recharts
- date-fns для работы с датами
- formik + yup для форм
- React Query для кеширования

### DevOps
- Docker для контейнеризации
- Docker Compose для оркестрации
- PostgreSQL 15+
- Nginx для статики

## Дополнительные фичи (nice to have)
- Темная тема
- Мультиязычность (i18n)
- Экспорт в CSV/Excel
- Импорт из CSV
- Push-уведомления через PWA
- Оффлайн режим с синхронизацией
- Интеграция с Telegram ботом (использовать существующую БД)

## Приоритеты
1. Работающая авторизация и базовый CRUD
2. Добавление/просмотр транзакций
3. Базовая аналитика (графики расходов)
4. PWA функционал
5. Остальные фичи

**Начни с создания backend структуры, миграций БД и базовых API endpoints для аутентификации и транзакций. Используй лучшие практики Go и следуй принципам чистой архитектуры.**