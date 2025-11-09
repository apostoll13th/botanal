"""
Configuration management for the expense tracking bot.
All environment variables and settings are centralized here.
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


class Config:
    """Main configuration class"""

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/expenses")

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "expense_bot.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Web Interface Configuration
    WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:8080")

    # Scheduled Tasks Configuration
    DAILY_REPORT_HOUR = int(os.getenv("DAILY_REPORT_HOUR", "21"))
    DAILY_REPORT_MINUTE = int(os.getenv("DAILY_REPORT_MINUTE", "0"))
    REMINDER_CHECK_HOUR = int(os.getenv("REMINDER_CHECK_HOUR", "9"))
    REMINDER_CHECK_MINUTE = int(os.getenv("REMINDER_CHECK_MINUTE", "0"))

    # Budget Alert Threshold (percentage)
    BUDGET_ALERT_THRESHOLD = float(os.getenv("BUDGET_ALERT_THRESHOLD", "80"))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не задан. Проверьте .env файл")
        return True


# Categories for expenses
CATEGORIES = [
    'Продукты',
    'Транспорт',
    'Развлечения',
    'Здоровье',
    'Одежда',
    'Дом',
    'Дети',
    'Прочее'
]

# Reminder frequencies
REMINDER_FREQUENCIES = [
    'Ежедневно',
    'Еженедельно',
    'Ежемесячно'
]

# Period mappings
PERIOD_LABEL_TO_CODE = {
    'Ежедневно': 'daily',
    'Еженедельно': 'weekly',
    'Ежемесячно': 'monthly'
}

CODE_TO_PERIOD_LABEL = {
    code: label for label, code in PERIOD_LABEL_TO_CODE.items()
}

# Conversation states
EXPENSE_AMOUNT = 0
EXPENSE_CATEGORY = 1
BUDGET_AMOUNT = 2
BUDGET_CATEGORY = 3
SAVINGS_AMOUNT = 4
SAVINGS_DESCRIPTION = 5
