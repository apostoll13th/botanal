#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
SERVICES=("backend" "bot")

echo "==> DATABASE_URL in .env"
if [[ -f "$ENV_FILE" ]]; then
  grep -E '^DATABASE_URL=' "$ENV_FILE" || echo "  (not set)"
else
  echo "  .env not found"
fi

echo ""

if ! command -v docker >/dev/null 2>&1; then
  echo "docker command not found. Skipping container checks."
  exit 0
fi

for svc in "${SERVICES[@]}"; do
  echo "==> $svc container"
  if ! docker compose ps --services 2>/dev/null | grep -q "^${svc}$"; then
    echo "  service '$svc' is not defined in docker-compose.yml"
    continue
  fi

  if ! docker compose ps "$svc" 2>/dev/null | grep -q "Up"; then
    echo "  service '$svc' is not running"
    continue
  fi

  docker compose exec -T "$svc" env | grep -E '^DATABASE_URL=' || echo "  DATABASE_URL not set inside container"
  echo ""
done
