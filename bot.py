"""
Main entry point for the Telegram expense tracking bot.
This file orchestrates all components and starts the bot.
"""

import logging
from datetime import time
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler

# Import configuration
from config import Config, BUDGET_AMOUNT, BUDGET_CATEGORY, SAVINGS_DESCRIPTION, SAVINGS_AMOUNT

# Import database components
from db import wait_for_db

# Import utilities
from utils import setup_logging

# Import all handlers
from handlers import (
    start, web_interface,
    add_expense_start, create_expense_handler,
    daily_report, weekly_report, monthly_report, detailed_monthly_report,
    set_budget_start, budget_amount, budget_category, save_budget, show_budgets,
    savings_goal_start, savings_description, savings_amount, show_savings_goals,
    process_savings_callback,
    set_reminder_start, show_reminders, process_reminder_callback,
    set_username, handle_general_messages,
    send_daily_reports, check_reminders,
    category_callback
)

# Setup logging
logger = setup_logging()


def create_budget_handler():
    """Create conversation handler for setting budgets"""
    return ConversationHandler(
        entry_points=[CommandHandler("set_budget", set_budget_start)],
        states={
            BUDGET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_amount)],
            BUDGET_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_category)],
            BUDGET_CATEGORY + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_budget)],
        },
        fallbacks=[],
    )


def create_savings_handler():
    """Create conversation handler for creating savings goals"""
    return ConversationHandler(
        entry_points=[CommandHandler("add_savings_goal", savings_goal_start)],
        states={
            SAVINGS_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, savings_description)],
            SAVINGS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, savings_amount)],
        },
        fallbacks=[],
    )


def setup_handlers(application: Application) -> None:
    """Setup all command and conversation handlers"""

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("web", web_interface))
    application.add_handler(CommandHandler("daily_report", daily_report))
    application.add_handler(CommandHandler("weekly_report", weekly_report))
    application.add_handler(CommandHandler("monthly_report", monthly_report))
    application.add_handler(CommandHandler("detailed_report", detailed_monthly_report))
    application.add_handler(CommandHandler("my_budgets", show_budgets))
    application.add_handler(CommandHandler("add_savings_goal", savings_goal_start))
    application.add_handler(CommandHandler("savings_goals", show_savings_goals))
    application.add_handler(CommandHandler("set_reminder", set_reminder_start))
    application.add_handler(CommandHandler("my_reminders", show_reminders))
    application.add_handler(CommandHandler("setname", set_username))

    # Обработчики для inline кнопок
    application.add_handler(CallbackQueryHandler(process_savings_callback, pattern="^add_to_goal_"))
    application.add_handler(CallbackQueryHandler(process_reminder_callback, pattern="^del_reminder_"))
    application.add_handler(CallbackQueryHandler(category_callback, pattern="^category_"))

    # Обработчики для conversation flows
    application.add_handler(create_expense_handler())
    application.add_handler(create_budget_handler())
    application.add_handler(create_savings_handler())

    # Обработчик общих сообщений (для напоминаний и пополнения целей)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_general_messages
    ))


def setup_scheduled_tasks(application: Application) -> None:
    """Setup scheduled tasks (reminders and daily reports)"""
    try:
        job_queue = application.job_queue

        # Настраиваем задания
        job_queue.run_daily(
            check_reminders,
            time=time(hour=Config.REMINDER_CHECK_HOUR, minute=Config.REMINDER_CHECK_MINUTE)
        )
        job_queue.run_daily(
            send_daily_reports,
            time=time(hour=Config.DAILY_REPORT_HOUR, minute=Config.DAILY_REPORT_MINUTE)
        )

        logger.info("Job queue configured successfully")
    except Exception as e:
        logger.warning(f"Cannot setup job queue: {e}")
        logger.warning("Install with: pip install 'python-telegram-bot[job-queue]'")
        logger.warning("Reminder and automatic report features will be unavailable")


def main() -> None:
    """Main entry point for the bot"""

    # Validate configuration
    Config.validate()

    # Wait for database and initialize structure
    logger.info("Waiting for database...")
    wait_for_db()

    logger.info("Database connection ready")

    # Create application
    logger.info("Creating bot application...")
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Setup handlers
    logger.info("Setting up handlers...")
    setup_handlers(application)

    # Setup scheduled tasks
    logger.info("Setting up scheduled tasks...")
    setup_scheduled_tasks(application)

    # Start the bot
    logger.info("Starting bot...")
    application.run_polling()


if __name__ == "__main__":
    main()
