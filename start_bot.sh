#!/bin/bash

# Скрипт для запуска Telegram бота

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Запуск Expense Tracking Bot ===${NC}"

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 не установлен!${NC}"
    exit 1
fi

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Виртуальное окружение не найдено. Создаю...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Виртуальное окружение создано${NC}"
fi

# Активация виртуального окружения
echo -e "${YELLOW}Активирую виртуальное окружение...${NC}"
source venv/bin/activate

# Установка зависимостей если requirements.txt изменился
if [ -f "requirements.txt" ]; then
    if [ ! -f ".last_requirements_hash" ] || [ "$(md5sum requirements.txt)" != "$(cat .last_requirements_hash 2>/dev/null)" ]; then
        echo -e "${YELLOW}Устанавливаю/обновляю зависимости...${NC}"
        pip install -r requirements.txt
        md5sum requirements.txt > .last_requirements_hash
    fi
fi

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo -e "${RED}Файл .env не найден!${NC}"
    echo -e "${YELLOW}Создаю .env из .env.example...${NC}"
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Пожалуйста, отредактируйте .env файл и добавьте ваш TELEGRAM_BOT_TOKEN${NC}"
        echo -e "${YELLOW}Используйте: nano .env${NC}"
        exit 1
    else
        echo -e "${RED}.env.example не найден!${NC}"
        exit 1
    fi
fi

# Проверка наличия токена
if ! grep -q "TELEGRAM_BOT_TOKEN=.*[^=]" .env; then
    echo -e "${RED}TELEGRAM_BOT_TOKEN не установлен в .env файле!${NC}"
    echo -e "${YELLOW}Пожалуйста, добавьте ваш токен бота в .env файл${NC}"
    exit 1
fi

# Создание директории для логов если её нет
LOG_DIR=$(grep "LOG_FILE=" .env | cut -d'=' -f2 | xargs dirname 2>/dev/null || echo ".")
if [ "$LOG_DIR" != "." ] && [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}Создаю директорию для логов: $LOG_DIR${NC}"
    mkdir -p "$LOG_DIR"
fi

# Запуск бота
echo -e "${GREEN}Запускаю бота...${NC}"
echo -e "${YELLOW}Для остановки используйте Ctrl+C${NC}"
echo -e "${GREEN}==============================${NC}"

python bot.py