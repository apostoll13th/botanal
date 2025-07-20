# Инструкция по развертыванию бота на Ubuntu Server

## Требования
- Ubuntu 20.04+ 
- Python 3.8+
- Доступ с правами sudo

## Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install python3-pip python3-venv git -y

# Создание пользователя для бота (опционально)
sudo useradd -m -s /bin/bash botuser
```

## Шаг 2: Клонирование и настройка проекта

```bash
# Переход в домашнюю директорию
cd /home/ubuntu

# Клонирование репозитория (или копирование файлов)
# git clone <your-repo-url> telega_bot
# или скопируйте файлы через scp/sftp

cd telega_bot

# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

## Шаг 3: Настройка конфигурации

```bash
# Создание .env файла из примера
cp .env.example .env

# Редактирование .env файла
nano .env
```

Добавьте ваш токен бота:
```
TELEGRAM_BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
LOG_LEVEL=INFO
LOG_FILE=/var/log/expense-bot/bot.log
```

## Шаг 4: Создание директории для логов

```bash
# Создание директории для логов
sudo mkdir -p /var/log/expense-bot
sudo chown ubuntu:ubuntu /var/log/expense-bot
```

## Шаг 5: Настройка systemd сервиса

```bash
# Копирование файла сервиса
sudo cp expense-bot.service /etc/systemd/system/

# Редактирование пути если необходимо
sudo nano /etc/systemd/system/expense-bot.service

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable expense-bot

# Запуск бота
sudo systemctl start expense-bot
```

## Шаг 6: Проверка работы

```bash
# Проверка статуса
sudo systemctl status expense-bot

# Просмотр логов
sudo journalctl -u expense-bot -f

# Или просмотр файла логов
tail -f /var/log/expense-bot/bot.log
```

## Управление ботом

```bash
# Остановка
sudo systemctl stop expense-bot

# Перезапуск
sudo systemctl restart expense-bot

# Просмотр логов
sudo journalctl -u expense-bot --since "1 hour ago"
```

## Обновление бота

```bash
# Остановка бота
sudo systemctl stop expense-bot

# Переход в директорию
cd /home/ubuntu/telega_bot

# Активация виртуального окружения
source venv/bin/activate

# Обновление кода (git pull или копирование новых файлов)

# Обновление зависимостей если необходимо
pip install -r requirements.txt

# Запуск бота
sudo systemctl start expense-bot
```

## Резервное копирование

База данных `expenses.db` содержит все данные пользователей. Регулярно создавайте резервные копии:

```bash
# Создание резервной копии
cp expenses.db expenses_backup_$(date +%Y%m%d_%H%M%S).db

# Автоматическое резервное копирование через cron
crontab -e
# Добавьте строку для ежедневного бэкапа в 3:00
0 3 * * * cp /home/ubuntu/telega_bot/expenses.db /home/ubuntu/backups/expenses_$(date +\%Y\%m\%d).db
```

## Безопасность

1. **Никогда не коммитьте .env файл в git**
2. Ограничьте права доступа к файлам:
   ```bash
   chmod 600 .env
   chmod 600 expenses.db
   ```
3. Используйте файрвол для ограничения доступа:
   ```bash
   sudo ufw allow ssh
   sudo ufw enable
   ```

## Устранение неполадок

1. **Бот не запускается**
   - Проверьте токен в .env файле
   - Проверьте логи: `sudo journalctl -u expense-bot -n 50`

2. **Ошибки с базой данных**
   - Проверьте права доступа к expenses.db
   - Убедитесь, что директория доступна для записи

3. **Проблемы с зависимостями**
   - Обновите pip: `pip install --upgrade pip`
   - Переустановите зависимости: `pip install -r requirements.txt --force-reinstall`

## Мониторинг

Для отслеживания работы бота можно настроить:

1. **Простой мониторинг через systemd**:
   ```bash
   # Проверка, что сервис активен
   systemctl is-active expense-bot
   ```

2. **Уведомления о падении сервиса**:
   Создайте файл `/etc/systemd/system/expense-bot-notify@.service`:
   ```ini
   [Unit]
   Description=Expense Bot failure notification

   [Service]
   Type=oneshot
   ExecStart=/usr/bin/mail -s "Expense Bot Failed" admin@example.com
   ```

   И добавьте в основной сервис:
   ```ini
   [Unit]
   OnFailure=expense-bot-notify@%n.service
   ```