# ✅ Инструкция по проверке сборки

## Быстрый тест исправлений

### 1. Очистите старые образы

```bash
# Остановите всё
docker compose down -v

# Удалите старые образы frontend
docker rmi telega_bot-frontend 2>/dev/null || true

# Очистите build cache (опционально)
docker builder prune -f
```

### 2. Пересоберите frontend

```bash
# Соберите только frontend с выводом логов
docker compose build --no-cache frontend

# Или соберите всё заново
docker compose build --no-cache
```

### 3. Запустите проект

```bash
docker compose up -d

# Следите за логами
docker compose logs -f
```

### 4. Проверьте что всё работает

```bash
# 1. Проверьте статус всех контейнеров (все должны быть Up)
docker compose ps

# Ожидаемый вывод:
# NAME                   STATUS
# telega_bot-backend-1   Up
# telega_bot-bot-1       Up
# telega_bot-db-1        Up
# telega_bot-frontend-1  Up

# 2. Проверьте backend API
curl http://localhost:5000/api/health

# Ожидаемый вывод: {"status":"ok"}

# 3. Проверьте frontend (должен вернуть HTML)
curl -I http://localhost:8080

# Ожидаемый вывод: HTTP/1.1 200 OK

# 4. Откройте в браузере
open http://localhost:8080?user_id=123456
```

## Что было исправлено

### ❌ Была ошибка:
```
ERROR [frontend builder 4/6] RUN npm ci --only=production
```

### ✅ Исправления:

1. **Изменен Dockerfile.frontend-react:**
   - `npm ci` → `npm install --legacy-peer-deps`
   - Добавлен `NODE_OPTIONS=--max-old-space-size=2048`
   - Оптимизирован порядок COPY для кэширования
   - Добавлен healthcheck

2. **Обновлен package.json:**
   - Добавлена зависимость `web-vitals`

3. **Создан TROUBLESHOOTING.md:**
   - Руководство по решению типичных проблем

## Если сборка не удалась

### Проверьте логи:
```bash
docker compose logs frontend
```

### Ищите такие строки (это успех):
```
Successfully built xxxxxx
Successfully tagged telega_bot-frontend:latest
```

### Если ошибка осталась:

1. **Проверьте Docker версию:**
```bash
docker --version
# Нужно: Docker version 20.10+
```

2. **Увеличьте память для Docker:**
   - Docker Desktop → Settings → Resources
   - Memory: минимум 4GB

3. **Попробуйте полную очистку:**
```bash
docker system prune -a
docker compose up --build
```

4. **См. полное руководство:**
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Ожидаемое время сборки

- **Первая сборка:** 5-10 минут
- **Последующие сборки:** 1-3 минуты (благодаря кэшу)

## Размеры образов

```bash
docker images | grep telega_bot

# Ожидаемые размеры:
# telega_bot-frontend   ~25MB  (Nginx + React build)
# telega_bot-backend    ~20MB  (Go binary)
# telega_bot-bot        ~150MB (Python + deps)
# telega_bot-db         ~230MB (PostgreSQL)
```

---

**Сборка прошла успешно? Переходите к [README.md](README.md) для полной инструкции!**
