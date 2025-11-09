#!/bin/bash

set -euo pipefail

echo "🚀 Запуск веб-интерфейса и API через Docker Compose"
echo "ℹ️  Убедитесь, что переменные окружения заданы в .env (см. .env.example)"

docker compose up --build frontend backend
