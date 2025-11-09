# Веб-интерфейс для Telegram бота учета финансов

## Описание

Веб-интерфейс предоставляет удобный доступ к статистике расходов через браузер. Включает:
- Круговые диаграммы и графики динамики
- Таблицы с фильтрацией
- Мониторинг бюджетов и целей
- Адаптивную верстку

## Структура проекта

```
telega_bot/
├── backend/           # Flask API сервер (Gunicorn в контейнере)
├── frontend/          # Статический интерфейс + nginx proxy /api
├── bot.py             # Telegram бот
├── db.py              # Подключение к PostgreSQL
├── docker-compose.yml # Оркестрация сервисов
└── Dockerfile.*       # Docker-образы для bot/backend/frontend
```

PostgreSQL поднимается отдельным контейнером `db`, данные сохраняются в volume `postgres_data`.

## Быстрый запуск (Docker Compose)

1. Создайте `.env` (можно из `.env.example`) и заполните:
   - `TELEGRAM_BOT_TOKEN`
   - при необходимости `WEB_APP_URL` (по умолчанию `http://localhost:8080`)

2. Поднимите весь стек:
   ```bash
   docker compose up --build
   ```

   Это запустит:
   - `db` — PostgreSQL 15 (`postgres/postgres`)
   - `backend` — Flask API (порт 5000)
   - `bot` — Telegram бот (использует те же переменные окружения)
   - `frontend` — Nginx со статикой и проксированием `/api` на backend (порт 8080)

3. Откройте http://localhost:8080/?user_id=<ваш Telegram ID> или воспользуйтесь кнопкой `/web` в боте.

Остановка:
```bash
docker compose down
```

## API Эндпоинты

- `GET /api/health` — проверка состояния
- `GET /api/user/<user_id>` — информация о пользователе
- `GET /api/expenses/<user_id>` + фильтры `start_date`, `end_date`, `category`
- `GET /api/expenses-summary/<user_id>` — агрегаты за 30 дней
- `GET /api/budgets/<user_id>` — текущие бюджеты
- `GET /api/goals/<user_id>` — цели накоплений

## Конфигурация

- `DATABASE_URL` — общий connection string для бота и backend (по умолчанию `postgresql://postgres:postgres@db:5432/expenses`)
- `WEB_APP_URL` — ссылка, которую бот отправляет пользователю в `/start` и `/web`
- Порты можно изменить в `docker-compose.yml`
- Frontend ходит к API по относительному пути `/api`, nginx проксирует его на сервис `backend`

### Доступ из локальной сети

1. Узнайте IP машины с docker (`ipconfig`/`ifconfig`)
2. Обновите `WEB_APP_URL` в `.env`, например `http://192.168.0.10:8080`
3. Пробросьте нужные порты или используйте reverse-proxy

## Типичные проблемы

- **Бот не подключается к БД** — проверьте `DATABASE_URL` и состояние контейнера `db` (`docker compose logs db`)
- **Нет данных на фронте** — убедитесь, что бота запущен и добавлены расходы, посмотрите консоль браузера
- **CORS/404** — nginx в контейнере `frontend` должен быть запущен, API доступен по `/api`

## Расширение функционала

- Добавление новых диаграмм: расширьте эндпоинты в `backend/app.py` и визуализации в `frontend/app.js`
- Экспорт данных: добавьте новые маршруты Flask и кнопки UI
- Авторизация: внедрите JWT/куки и защищайте эндпоинты

## Скриншоты

После запуска доступны вкладки:
- **Обзор** — круговая диаграмма + график динамики
- **Расходы** — таблица с фильтрами по дате/категории
- **Бюджеты** — прогресс-бары по категориям
- **Цели** — карточки накоплений
