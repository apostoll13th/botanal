"""
Utility functions for the expense tracking bot.
Includes chart generation, keyboards, and helper functions.
"""

import logging
import io
from typing import Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_monthly_expenses
from config import Config

logger = logging.getLogger(__name__)

# Установка русских шрифтов для matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['font.size'] = 12


def build_web_url(user_id: int) -> str:
    """Build web interface URL with user_id parameter"""
    separator = '&' if '?' in Config.WEB_APP_URL else '?'
    return f"{Config.WEB_APP_URL}{separator}user_id={user_id}"


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard with bot commands"""
    return ReplyKeyboardMarkup([
        ['/add_expense', '/delete_last'],
        ['/daily_report', '/weekly_report', '/monthly_report'],
        ['/detailed_report', '/my_budgets'],
        ['/savings_goals', '/set_reminder', '/reset_password']
    ], resize_keyboard=True)


def is_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if the message is a command for the bot.
    In private chats, all messages are processed.
    In group chats, only process:
    - Commands (starting with /)
    - Replies to bot messages
    - Messages mentioning the bot
    """
    message = update.message

    if not message or not message.text:
        return False

    # В приватном чате обрабатываем все сообщения
    if message.chat.type == 'private':
        return True

    text = message.text

    # Команды
    if text.startswith('/'):
        return True

    # Ответ на сообщение бота
    if message.reply_to_message and message.reply_to_message.from_user.is_bot:
        return True

    # Упоминание бота по имени
    bot_username = context.bot.username
    if bot_username and f"@{bot_username}" in text:
        return True

    return False


def create_monthly_chart(user_id: int) -> Optional[io.BytesIO]:
    """
    Create a pie chart for monthly expenses by category.
    Returns a BytesIO buffer with the chart image or None if no data.
    """
    expenses, _ = get_monthly_expenses(user_id)

    if not expenses:
        logger.warning("No expense data for creating chart")
        return None

    # Преобразуем строки БД в словари для корректной работы с pandas
    expenses_dict = []
    for expense in expenses:
        total_value = float(expense['total']) if expense['total'] is not None else 0
        expense_dict = {'category': expense['category'], 'total': total_value}
        expenses_dict.append(expense_dict)

    logger.info(f"Transformed data for chart: {expenses_dict}")

    # Если после преобразования нет данных, возвращаем None
    if not expenses_dict:
        logger.warning("No data after transformation for chart")
        return None

    # Создаем DataFrame из списка словарей
    df = pd.DataFrame(expenses_dict)

    # Проверяем наличие данных
    if df.empty:
        logger.warning("DataFrame is empty after creation")
        return None

    # Создаем круговую диаграмму
    plt.figure(figsize=(10, 6))
    plt.pie(df['total'], labels=df['category'], autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Равные пропорции для круговой диаграммы
    plt.title('Общие расходы семьи за месяц по категориям')

    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return buf


def setup_logging() -> logging.Logger:
    """
    Setup logging configuration for the bot.
    Returns configured logger instance.
    """
    from logging.handlers import RotatingFileHandler

    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(log_formatter)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    # Настройка корневого логгера
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Отключение debug логов от matplotlib
    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    return logger


def format_expense_report(expenses: list, total: float, period: str = "сегодня") -> str:
    """
    Format expense report as a text message.

    Args:
        expenses: List of expense records
        total: Total amount
        period: Period description (default: "сегодня")

    Returns:
        Formatted report string
    """
    if not expenses:
        return f'За {period} пока нет расходов.'

    report = f"Расходы за {period}:\n\n"
    for expense in expenses:
        total_value = float(expense['total']) if expense['total'] else 0
        report += f"{expense['category']}: {total_value:.2f} руб."

        # Проверяем наличие ключа user_name перед использованием
        if 'user_name' in expense and expense['user_name']:
            report += f" (добавил: {expense['user_name']})"

        report += "\n"

    report += f"\nОбщая сумма: {total:.2f} руб."
    return report


def format_budget_report(budgets: list, user_id: int) -> str:
    """
    Format budget report with current status.

    Args:
        budgets: List of budget records
        user_id: User ID for checking budget status

    Returns:
        Formatted report string
    """
    from database import check_budget_status
    from config import CODE_TO_PERIOD_LABEL

    if not budgets:
        return 'У вас пока нет установленных бюджетов.'

    report = "Ваши бюджеты:\n\n"

    for budget in budgets:
        category = budget['category']
        amount = float(budget['amount']) if budget['amount'] is not None else 0
        period = budget['period']
        period_label = CODE_TO_PERIOD_LABEL.get(period, period)

        _, spent, percentage = check_budget_status(user_id, category, period)

        report += f"🔹 {category} ({period_label}): {spent:.2f} / {amount:.2f} руб. ({percentage:.1f}%)\n"

    return report


def format_savings_goals_report(goals: list) -> str:
    """
    Format savings goals report.

    Args:
        goals: List of savings goal records

    Returns:
        Formatted report string
    """
    if not goals:
        return 'У вас пока нет целей экономии.'

    report = "Ваши цели экономии:\n\n"

    for goal in goals:
        description = goal['description']
        target = goal['target_amount']
        current = goal['current_amount'] or 0
        percentage = (current / target) * 100 if target > 0 else 0

        report += f"🎯 {description}: {current:.2f} / {target:.2f} руб. ({percentage:.1f}%)\n"

    return report


def format_reminders_report(reminders: list) -> str:
    """
    Format reminders report.

    Args:
        reminders: List of reminder records

    Returns:
        Formatted report string
    """
    if not reminders:
        return 'У вас пока нет напоминаний.'

    report = "Ваши напоминания:\n\n"

    for reminder in reminders:
        report += f"⏰ {reminder['message']} ({reminder['frequency']})\n"

    return report


def format_detailed_monthly_report(expenses: list) -> str:
    """
    Format detailed monthly report with breakdown by users.

    Args:
        expenses: List of expense records grouped by user

    Returns:
        Formatted report string
    """
    if not expenses:
        return 'За последний месяц нет расходов.'

    report = "📊 Детальный отчет по пользователям за 30 дней:\n\n"

    current_user = None
    user_total = 0
    grand_total = 0

    for expense in expenses:
        user_name = expense['user_name'] if expense['user_name'] else "Неизвестный"
        amount = float(expense['total']) if expense['total'] else 0

        if current_user != user_name:
            if current_user is not None:
                report += f"  💳 Итого {current_user}: {user_total:.2f} руб.\n\n"
            current_user = user_name
            user_total = 0
            report += f"👤 {user_name}:\n"

        report += f"  • {expense['category']}: {amount:.2f} руб.\n"
        user_total += amount
        grand_total += amount

    if current_user is not None:
        report += f"  💳 Итого {current_user}: {user_total:.2f} руб.\n\n"

    report += f"💰 Общая сумма семьи: {grand_total:.2f} руб."

    return report
