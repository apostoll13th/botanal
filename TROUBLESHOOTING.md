# 🔧 Troubleshooting Guide

Решение типичных проблем при развертывании Telegram Expense Tracker.

## 🐳 Проблемы с Docker Build

### ❌ Error: `npm ci --only=production` failed

**Симптом:**
```
ERROR [frontend builder 4/6] RUN npm ci --only=production
```

**Причина:**
Отсутствует `package-lock.json` или несовместимость версий пакетов.

**Решение:**
✅ Уже исправлено в Dockerfile - используется `npm install --legacy-peer-deps`

Если проблема сохраняется:
```bash
# Очистите Docker cache
docker system prune -a

# Пересоберите без кэша
docker compose build --no-cache frontend
```

---

### ❌ Error: Out of memory during build

**Симптом:**
```
JavaScript heap out of memory
```

**Решение:**
✅ Уже исправлено - добавлен `NODE_OPTIONS=--max-old-space-size=2048`

Если нужно больше памяти для Docker:
```bash
# Docker Desktop -> Settings -> Resources
# Увеличьте Memory до 4GB+
```

---

### ❌ Error: ENOENT no such file or directory

**Симптом:**
```
COPY failed: file not found
```

**Решение:**
Проверьте структуру файлов:
```bash
# Должны быть эти директории:
ls frontend-react/
# public/  src/  package.json  nginx.conf

ls backend-go/
# main.go  go.mod  go.sum
```

---

## 🔌 Проблемы с портами

### ❌ Port is already allocated

**Симптом:**
```
Error: bind: address already in use
```

**Решение:**

1. **Найдите процесс на порту:**
```bash
# Для порта 8080
lsof -i :8080

# Для порта 5000
lsof -i :5000
```

2. **Остановите процесс или измените порт:**

В `docker-compose.yml`:
```yaml
frontend:
  ports:
    - "8081:80"  # вместо 8080

backend:
  ports:
    - "5001:5000"  # вместо 5000
```

---

## 🗄️ Проблемы с базой данных

### ❌ Database connection refused

**Симптом:**
```
Error: connection refused at db:5432
```

**Решение:**

1. **Проверьте что БД запущена:**
```bash
docker compose ps
# db должен быть Up
```

2. **Дождитесь инициализации БД:**
```bash
docker compose logs db
# Ждите: "database system is ready to accept connections"
```

3. **Перезапустите сервисы:**
```bash
docker compose restart backend bot
```

---

### ❌ Tables don't exist

**Симптом:**
```
ERROR: relation "expenses" does not exist
```

**Решение:**

1. **Проверьте миграции:**
```bash
docker compose logs bot | grep -i migration
```

2. **Пересоздайте БД:**
```bash
docker compose down -v  # ВНИМАНИЕ: удалит все данные!
docker compose up -d db
# Подождите 10 секунд
docker compose up bot backend
```

---

## 🤖 Проблемы с Telegram Bot

### ❌ Bot не отвечает

**Симптом:**
Bot не реагирует на команды в Telegram.

**Решение:**

1. **Проверьте токен:**
```bash
docker compose exec bot env | grep TELEGRAM_BOT_TOKEN
# Должен быть ваш реальный токен
```

2. **Проверьте логи бота:**
```bash
docker compose logs bot
# Ищите ошибки подключения
```

3. **Перезапустите бота:**
```bash
docker compose restart bot
```

---

### ❌ TELEGRAM_BOT_TOKEN не задан

**Симптом:**
```
ValueError: TELEGRAM_BOT_TOKEN не задан
```

**Решение:**

1. **Создайте .env файл:**
```bash
cp .env.example .env
```

2. **Добавьте токен:**
```bash
echo "TELEGRAM_BOT_TOKEN=ваш_токен_сюда" >> .env
```

3. **Перезапустите:**
```bash
docker compose down
docker compose up -d
```

---

## 🌐 Проблемы с Frontend

### ❌ API requests fail with CORS error

**Симптом:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Решение:**

✅ В production используйте Nginx proxy (уже настроен):
```
http://localhost:8080/api -> http://backend:5000/api
```

Для разработки добавьте в backend CORS:
```go
// Уже добавлено в main.go
config.AllowAllOrigins = true
```

---

### ❌ Blank page / React not loading

**Симптом:**
Открывается пустая страница или ошибка в консоли браузера.

**Решение:**

1. **Проверьте консоль браузера (F12):**
```
Ищите JavaScript ошибки
```

2. **Проверьте что user_id в URL:**
```
http://localhost:8080?user_id=123456
```

3. **Проверьте что backend доступен:**
```bash
curl http://localhost:5000/api/health
# Должно быть: {"status":"ok"}
```

4. **Пересоберите frontend:**
```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

---

### ❌ Charts not displaying

**Симптом:**
Графики не отображаются, но данные есть.

**Решение:**

Проверьте что Chart.js загружен:
```bash
# В консоли браузера (F12):
console.log(Chart)
# Должен вывести объект Chart
```

Очистите cache браузера: `Ctrl+Shift+R` (или `Cmd+Shift+R` на Mac)

---

## 🔧 Общие проблемы

### ❌ Docker daemon not running

**Симптом:**
```
Cannot connect to Docker daemon
```

**Решение:**
```bash
# Mac/Windows:
# Запустите Docker Desktop

# Linux:
sudo systemctl start docker
```

---

### ❌ Permission denied

**Симптом:**
```
Permission denied while trying to connect to Docker daemon
```

**Решение:**
```bash
# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиньтесь или выполните:
newgrp docker
```

---

### ❌ Disk space issues

**Симптом:**
```
No space left on device
```

**Решение:**
```bash
# Очистите неиспользуемые образы и контейнеры
docker system prune -a

# Очистите volumes (ОСТОРОЖНО: удалит данные БД!)
docker volume prune
```

---

## 📊 Диагностика

### Проверка всех сервисов

```bash
# 1. Статус контейнеров
docker compose ps

# 2. Логи всех сервисов
docker compose logs

# 3. Проверка сети
docker network inspect telega_bot_default

# 4. Проверка БД
docker compose exec db psql -U postgres -d expenses -c "\dt"

# 5. Проверка API
curl http://localhost:5000/api/health

# 6. Проверка Frontend
curl http://localhost:8080
```

---

## 🆘 Полный сброс

Если ничего не помогает:

```bash
# 1. Остановить всё
docker compose down -v

# 2. Удалить образы
docker rmi $(docker images -q telega_bot*)

# 3. Очистить Docker cache
docker system prune -a

# 4. Заново собрать
docker compose up --build

# 5. Проверить логи
docker compose logs -f
```

---

## 📞 Поддержка

Если проблема не решена:

1. Соберите диагностическую информацию:
```bash
docker compose ps > debug.txt
docker compose logs >> debug.txt
docker version >> debug.txt
```

2. Создайте Issue в репозитории с приложением `debug.txt`

3. Опишите:
   - Что пытались сделать
   - Что ожидали
   - Что получили (ошибка)
   - Ваша ОС и версия Docker

---

**Последнее обновление:** 2024-11-09
