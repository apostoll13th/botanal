"""
Command and conversation handlers for the expense tracking bot.
Contains all bot interaction logic.
"""

import logging
import re
import secrets
import string
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from database import (
    add_expense, get_daily_expenses, get_weekly_expenses, get_monthly_expenses,
    check_budget_alerts, set_budget, get_budgets,
    add_savings_goal, get_savings_goals, update_savings_progress,
    add_reminder, get_reminders, delete_reminder,
    save_user, get_user_name, get_all_users, get_detailed_monthly_expenses,
    get_available_categories, get_app_user_by_telegram_id,
    create_portal_user, reset_app_user_password
)
from utils import (
    build_web_url, get_main_keyboard, is_bot_command, create_monthly_chart,
    format_expense_report, format_budget_report, format_savings_goals_report,
    format_reminders_report, format_detailed_monthly_report
)
from config import (
    REMINDER_FREQUENCIES, PERIOD_LABEL_TO_CODE,
    CODE_TO_PERIOD_LABEL, EXPENSE_AMOUNT, EXPENSE_CATEGORY,
    BUDGET_AMOUNT, BUDGET_CATEGORY, SAVINGS_AMOUNT, SAVINGS_DESCRIPTION
)

logger = logging.getLogger(__name__)


def get_dynamic_categories():
    categories = get_available_categories()
    return categories if categories else ["Прочее"]


# ========== START AND WEB INTERFACE ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user_id = update.effective_user.id

    full_name = update.effective_user.full_name or update.effective_user.first_name or update.effective_user.username or "Пользователь"
    context.user_data['user_name'] = full_name
    save_user(user_id, full_name)

    # Создаем инлайн-кнопку для веб-интерфейса
    web_url = build_web_url(user_id)
    inline_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Открыть личный кабинет", url=web_url)]
    ])

    await update.message.reply_text(
        'Привет! Я бот для учета расходов. Вот что я умею:\n\n'
        '• Добавление и отслеживание расходов\n'
        '• Ежедневные, еженедельные и месячные отчеты\n'
        '• Установка бюджетов по категориям\n'
        '• Создание целей экономии\n'
        '• Настройка напоминаний\n\n'
        'Используйте кнопки ниже для доступа к функциям.',
        reply_markup=get_main_keyboard()
    )

    # Отправляем отдельное сообщение с веб-интерфейсом
    await update.message.reply_text(
        '🚀 Новинка! Теперь вы можете просматривать свою статистику в удобном веб-интерфейсе:',
        reply_markup=inline_keyboard
    )

    portal_message = build_portal_message(update.effective_user, full_name)
    await update.message.reply_text(portal_message, reply_markup=get_main_keyboard())


async def web_interface(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /web command"""
    user_id = update.effective_user.id
    web_url = build_web_url(user_id)

    inline_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Открыть личный кабинет", url=web_url)]
    ])

    await update.message.reply_text(
        '📊 Веб-интерфейс позволяет:\n\n'
        '• Просматривать графики расходов\n'
        '• Анализировать статистику по категориям\n'
        '• Отслеживать прогресс по бюджетам и целям\n'
        '• Фильтровать операции по датам\n\n'
        'Нажмите кнопку ниже для перехода:',
        reply_markup=inline_keyboard
    )


# ========== EXPENSE HANDLERS ==========

async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start adding an expense"""
    await update.message.reply_text('Введите сумму расхода:')
    return EXPENSE_AMOUNT


async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle expense amount input"""
    user_input = update.message.text
    try:
        amount = float(user_input)
        context.user_data['amount'] = amount

        # Создаем ИНЛАЙН-клавиатуру с категориями (работает в группах)
        categories = get_dynamic_categories()
        keyboard = []
        row = []
        for i, category in enumerate(categories):
            row.append(InlineKeyboardButton(category, callback_data=f"category_{category}"))
            if (i + 1) % 3 == 0 or i == len(categories) - 1:
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['available_categories'] = categories

        await update.message.reply_text('Выберите категорию:', reply_markup=reply_markup)
        return EXPENSE_CATEGORY
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите корректную сумму числом.')
        return EXPENSE_AMOUNT


async def expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle expense category (text input - for backward compatibility)"""
    category = update.message.text.strip()
    categories = context.user_data.get('available_categories') or get_dynamic_categories()
    if category not in categories:
        await update.message.reply_text(
            "Такой категории нет в справочнике. Пожалуйста, выберите одну из предложенных кнопок или добавьте категорию через веб-интерфейс."
        )
        return EXPENSE_CATEGORY

    user_id = update.effective_user.id
    amount = context.user_data['amount']

    add_expense(user_id, amount, category)

    # Проверяем превышение бюджета
    budget_alerts = check_budget_alerts(user_id, category, amount)

    # Основное сообщение о добавлении расхода
    message = f'✅ Расход добавлен: {amount} руб. в категорию "{category}"'

    # Если есть предупреждения о бюджете, добавляем их к сообщению
    if budget_alerts:
        message += "\n\n⚠️ Внимание! Вы приближаетесь к лимиту бюджета:"
        for alert in budget_alerts:
            message += f"\n• {alert['period']}: потрачено {alert['spent']:.2f} из {alert['budget']:.2f} руб. ({alert['percentage']:.1f}%)"

    # Возвращаем основное меню
    await update.message.reply_text(message, reply_markup=get_main_keyboard())
    return ConversationHandler.END


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection via inline keyboard"""
    query = update.callback_query
    await query.answer()

    # Проверяем на отмену
    if query.data == "category_cancel":
        await query.edit_message_text("❌ Добавление расхода отменено")
        context.user_data.pop('amount', None)
        return ConversationHandler.END

    # Проверяем корректность callback_data
    if not query.data.startswith("category_"):
        await query.edit_message_text("❌ Ошибка выбора категории")
        return ConversationHandler.END

    categories = context.user_data.get('available_categories') or get_dynamic_categories()

    # Получаем выбранную категорию из callback_data
    category = query.data.replace("category_", "")
    if category not in categories:
        await query.edit_message_text("❌ Такая категория недоступна. Попробуйте снова, используя свежий список.")
        return ConversationHandler.END

    user_id = update.effective_user.id
    amount = context.user_data.get('amount', 0)

    # Получаем имя пользователя из контекста или БД
    user_name = context.user_data.get('user_name', None)

    if not user_name:
        # Пытаемся получить имя из базы данных
        user_name = get_user_name(user_id)
        if user_name:
            # Сохраняем в контекст для будущего использования
            context.user_data['user_name'] = user_name

    # Добавляем расход
    add_expense(user_id, amount, category)

    # Проверяем превышение бюджета
    budget_alerts = check_budget_alerts(user_id, category, amount)

    # Основное сообщение о добавлении расхода
    message = f'✅ Расход добавлен: {amount} руб. в категорию "{category}"'
    if user_name:
        message += f' (добавил: {user_name})'

    # Если есть предупреждения о бюджете, добавляем их к сообщению
    if budget_alerts:
        message += "\n\n⚠️ Внимание! Вы приближаетесь к лимиту бюджета:"
        for alert in budget_alerts:
            message += f"\n• {alert['period']}: потрачено {alert['spent']:.2f} из {alert['budget']:.2f} руб. ({alert['percentage']:.1f}%)"

    # Обновляем сообщение
    await query.edit_message_text(message)

    return ConversationHandler.END


def create_expense_handler():
    """Create conversation handler for adding expenses"""
    return ConversationHandler(
        entry_points=[CommandHandler("add_expense", add_expense_start)],
        states={
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)],
            EXPENSE_CATEGORY: [
                CallbackQueryHandler(category_callback, pattern="^category_")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            CommandHandler("start", cancel_conversation)
        ],
        allow_reentry=True,
        per_chat=True,
        per_user=True
    )


# ========== REPORT HANDLERS ==========

async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /daily_report command"""
    user_id = update.effective_user.id
    expenses, total = get_daily_expenses(user_id)

    report = format_expense_report(expenses, total, "сегодня")
    await update.message.reply_text(report, reply_markup=get_main_keyboard())


async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /weekly_report command"""
    user_id = update.effective_user.id
    expenses, total = get_weekly_expenses(user_id)

    if not expenses:
        await update.message.reply_text('За последнюю неделю нет расходов.', reply_markup=get_main_keyboard())
        return

    report = "Расходы за последние 7 дней:\n\n"
    for expense in expenses:
        total_value = float(expense['total']) if expense['total'] else 0
        report += f"{expense['date']}: {total_value:.2f} руб.\n"

    report += f"\nОбщая сумма за неделю: {total:.2f} руб."
    await update.message.reply_text(report, reply_markup=get_main_keyboard())


async def monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /monthly_report command"""
    user_id = update.effective_user.id
    expenses, total = get_monthly_expenses(user_id)

    if not expenses:
        await update.message.reply_text('За последний месяц нет расходов.', reply_markup=get_main_keyboard())
        return

    report = "Расходы за последние 30 дней:\n\n"
    for expense in expenses:
        total_value = float(expense['total']) if expense['total'] else 0
        report += f"{expense['category']}: {total_value:.2f} руб.\n"

    report += f"\nОбщая сумма за месяц: {total:.2f} руб."
    await update.message.reply_text(report, reply_markup=get_main_keyboard())

    # Отправляем график расходов
    chart = create_monthly_chart(user_id)
    if chart:
        await update.message.reply_photo(chart, reply_markup=get_main_keyboard())


async def detailed_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /detailed_report command - show expenses by user"""
    expenses = get_detailed_monthly_expenses()
    report = format_detailed_monthly_report(expenses)
    await update.message.reply_text(report, reply_markup=get_main_keyboard())


# ========== BUDGET HANDLERS ==========

async def set_budget_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start setting a budget"""
    from telegram import ReplyKeyboardMarkup

    # Создаем клавиатуру с периодами
    keyboard = [[period] for period in ['Ежедневно', 'Еженедельно', 'Ежемесячно']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        'Установка бюджета. Выберите период:',
        reply_markup=reply_markup
    )

    return BUDGET_AMOUNT


async def budget_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle budget period selection"""
    period_label = update.message.text
    period_code = PERIOD_LABEL_TO_CODE.get(period_label, period_label)
    context.user_data['budget_period'] = period_code
    context.user_data['budget_period_label'] = CODE_TO_PERIOD_LABEL.get(period_code, period_label)

    await update.message.reply_text(f'Выбран период: {period_label}\nВведите сумму бюджета:')
    return BUDGET_CATEGORY


async def budget_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle budget amount input"""
    from telegram import ReplyKeyboardMarkup

    user_input = update.message.text
    try:
        amount = float(user_input)
        context.user_data['budget_amount'] = amount

        # Создаем клавиатуру с категориями
        keyboard = [[category] for category in CATEGORIES]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text('Выберите категорию для бюджета:', reply_markup=reply_markup)
        return BUDGET_CATEGORY + 1
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите корректную сумму числом.')
        return BUDGET_CATEGORY


async def save_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the budget"""
    category = update.message.text
    user_id = update.effective_user.id
    amount = context.user_data['budget_amount']
    period = context.user_data['budget_period']
    period_label = context.user_data.get('budget_period_label', CODE_TO_PERIOD_LABEL.get(period, period))

    set_budget(user_id, category, amount, period)

    # Возвращаем основное меню
    await update.message.reply_text(
        f'Бюджет установлен: {amount} руб. для категории "{category}" ({period_label})',
        reply_markup=get_main_keyboard()
    )

    return ConversationHandler.END


async def show_budgets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /my_budgets command"""
    user_id = update.effective_user.id
    budgets = get_budgets(user_id)

    report = format_budget_report(budgets, user_id)
    await update.message.reply_text(report, reply_markup=get_main_keyboard())


# ========== SAVINGS GOAL HANDLERS ==========

async def savings_goal_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start creating a savings goal"""
    await update.message.reply_text('Создание цели экономии. Введите описание цели:')
    return SAVINGS_DESCRIPTION


async def savings_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle savings goal description input"""
    description = update.message.text
    context.user_data['savings_description'] = description

    await update.message.reply_text('Введите целевую сумму:')
    return SAVINGS_AMOUNT


async def savings_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle savings goal amount input"""
    user_input = update.message.text
    try:
        amount = float(user_input)
        user_id = update.effective_user.id
        description = context.user_data['savings_description']

        add_savings_goal(user_id, description, amount)

        # Возвращаем основное меню
        await update.message.reply_text(
            f'Цель экономии создана: "{description}" на сумму {amount} руб.',
            reply_markup=get_main_keyboard()
        )

        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите корректную сумму числом.')
        return SAVINGS_AMOUNT


async def show_savings_goals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /savings_goals command"""
    user_id = update.effective_user.id
    goals = get_savings_goals(user_id)

    if not goals:
        await update.message.reply_text('У вас пока нет целей экономии.', reply_markup=get_main_keyboard())
        return

    report = format_savings_goals_report(goals)

    keyboard = []
    for goal in goals:
        keyboard.append([InlineKeyboardButton(
            f"Пополнить '{goal['description']}'",
            callback_data=f"add_to_goal_{goal['id']}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(report, reply_markup=reply_markup)


async def add_to_savings_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle adding money to a savings goal"""
    user_input = update.message.text
    try:
        amount = float(user_input)
        user_id = update.effective_user.id
        goal_id = context.user_data.get('current_goal_id')

        if goal_id:
            update_savings_progress(user_id, goal_id, amount)
            await update.message.reply_text(
                f'✅ Добавлено {amount} руб. к цели экономии.',
                reply_markup=get_main_keyboard()
            )
            context.user_data.pop('current_goal_id', None)
        else:
            await update.message.reply_text(
                'Ошибка: не найдена цель для пополнения.',
                reply_markup=get_main_keyboard()
            )
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите корректную сумму числом.')


async def process_savings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle savings goal callback buttons"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("add_to_goal_"):
        goal_id = int(query.data.split("_")[-1])
        context.user_data['current_goal_id'] = goal_id

        await query.message.reply_text("Введите сумму для пополнения цели:")


# ========== REMINDER HANDLERS ==========

async def set_reminder_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /set_reminder command"""
    await update.message.reply_text('Введите текст напоминания:')
    context.user_data['reminder_stage'] = 'text'


async def process_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process reminder creation"""
    from telegram import ReplyKeyboardMarkup

    user_id = update.effective_user.id
    text = update.message.text

    stage = context.user_data.get('reminder_stage', 'text')

    if stage == 'text':
        context.user_data['reminder_text'] = text
        context.user_data['reminder_stage'] = 'frequency'

        # Создаем клавиатуру с частотами
        keyboard = [[freq] for freq in REMINDER_FREQUENCIES]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text('Выберите частоту напоминания:', reply_markup=reply_markup)
    elif stage == 'frequency':
        frequency = text
        reminder_text = context.user_data.get('reminder_text', 'Напоминание')

        add_reminder(user_id, reminder_text, frequency)

        # Возвращаем основное меню
        await update.message.reply_text(
            f'Напоминание создано: "{reminder_text}" ({frequency})',
            reply_markup=get_main_keyboard()
        )

        context.user_data.pop('reminder_stage', None)
        context.user_data.pop('reminder_text', None)


async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /my_reminders command"""
    user_id = update.effective_user.id
    reminders = get_reminders(user_id)

    if not reminders:
        await update.message.reply_text('У вас пока нет напоминаний.', reply_markup=get_main_keyboard())
        return

    report = format_reminders_report(reminders)

    keyboard = []
    for reminder in reminders:
        keyboard.append([InlineKeyboardButton(
            f"Удалить '{reminder['message'][:20]}..'",
            callback_data=f"del_reminder_{reminder['id']}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(report, reply_markup=reply_markup)


async def process_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reminder callback buttons"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("del_reminder_"):
        reminder_id = int(query.data.split("_")[-1])
        user_id = update.effective_user.id

        delete_reminder(user_id, reminder_id)

        await query.message.reply_text("Напоминание удалено.", reply_markup=get_main_keyboard())


# ========== USER MANAGEMENT ==========

async def set_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setname command"""
    if not context.args:
        await update.message.reply_text(
            'Пожалуйста, укажите ваше имя после команды. Например: /setname Иван',
            reply_markup=get_main_keyboard()
        )
        return

    user_name = ' '.join(context.args)
    user_id = update.effective_user.id

    # Сохраняем имя пользователя в базе данных и контексте
    context.user_data['user_name'] = user_name
    save_user(user_id, user_name)

    await update.message.reply_text(
        f'Ваше имя установлено: {user_name}',
        reply_markup=get_main_keyboard()
    )


async def reset_portal_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset or create portal password for current user"""
    user = update.effective_user
    user_id = user.id
    new_password = generate_password()

    login = reset_app_user_password(user_id, new_password)
    if not login:
        # create a new account automatically
        full_name = user.full_name or user.first_name or user.username or "Пользователь"
        login_candidate = sanitize_login(user.username, user_id)
        try:
            create_portal_user(login_candidate, new_password, user_id, full_name)
            login = login_candidate
        except ValueError:
            login = f"user{user_id}"
            create_portal_user(login, new_password, user_id, full_name)

    await update.message.reply_text(
        "✅ Пароль для веб-кабинета сброшен.\n"
        f"Логин: {login}\n"
        f"Новый пароль: {new_password}",
        reply_markup=get_main_keyboard()
    )


# ========== SCHEDULED TASKS ==========

async def send_daily_reports(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send daily reports to all users (scheduled task)"""
    users = get_all_users()

    for user in users:
        user_id = user['user_id']
        expenses, total = get_daily_expenses(user_id)

        if expenses:
            report = "📊 Ежедневный отчет о расходах:\n\n"
            for expense in expenses:
                total_value = float(expense['total']) if expense['total'] else 0
                report += f"{expense['category']}: {total_value:.2f} руб.\n"

            report += f"\nОбщая сумма за сегодня: {total:.2f} руб."

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=report
                )
            except Exception as e:
                logger.error(f"Error sending daily report to user {user_id}: {e}")


async def check_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check and send reminders (scheduled task)"""
    from database import get_todays_reminders

    reminders = get_todays_reminders()

    for reminder in reminders:
        try:
            await context.bot.send_message(
                chat_id=reminder['user_id'],
                text=f"📣 Напоминание: {reminder['message']}"
            )
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")


# ========== GENERAL MESSAGE HANDLER ==========

async def handle_general_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general messages - only for bot commands"""

    # Проверяем, является ли это командой для бота
    if not is_bot_command(update, context):
        return  # Игнорируем сообщение

    # Проверяем состояние пользователя
    user_data = context.user_data

    # Если ожидается пополнение цели экономии
    if 'current_goal_id' in user_data:
        await add_to_savings_goal(update, context)
        return

    # Если ожидается ввод данных для напоминания
    elif 'reminder_stage' in user_data:
        await process_reminder(update, context)
        return

    # Если ничего не ожидается, игнорируем сообщение


# ========== UTILITY HANDLERS ==========

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current conversation"""
    await update.message.reply_text(
        'Операция отменена.',
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END
def generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def sanitize_login(username: Optional[str], user_id: int) -> str:
    if username:
        candidate = re.sub(r'[^a-z0-9_]', '', username.lower())
        if candidate:
            return candidate
    return f"user{user_id}"


def build_portal_message(user, full_name: str) -> str:
    existing = get_app_user_by_telegram_id(user.id)
    if existing:
        return (
            "🔑 Доступ к веб-кабинету уже создан.\n"
            f"Логин: {existing['login']}\n"
            "Если забыли пароль, используйте команду /reset_password."
        )

    login = sanitize_login(user.username, user.id)
    password = generate_password()
    try:
        create_portal_user(login, password, user.id, full_name)
    except ValueError:
        login = f"user{user.id}"
        password = generate_password()
        create_portal_user(login, password, user.id, full_name)

    return (
        "🎉 Создан доступ в веб-кабинет!\n"
        f"Логин: {login}\n"
        f"Пароль: {password}\n"
        "Сохраните данные или сразу измените пароль в UI."
    )
