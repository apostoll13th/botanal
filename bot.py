import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from datetime import datetime, timedelta, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import pandas as pd
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from database_migrations import check_and_update_database
from db import get_db_connection, wait_for_db
from db_schema import init_db, update_database_structure

# Установка русских шрифтов
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['font.size'] = 12

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "expense_bot.log")
WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:8080")

if not TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN не задан. Проверьте .env")


def build_web_url(user_id: int) -> str:
    separator = '&' if '?' in WEB_APP_URL else '?'
    return f"{WEB_APP_URL}{separator}user_id={user_id}"

# Настройка логирования
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Файловый обработчик с ротацией
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)

# Консольный обработчик
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Настройка корневого логгера
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Отключение debug логов от matplotlib
logging.getLogger('matplotlib').setLevel(logging.WARNING)

# Состояния для ConversationHandler
EXPENSE_AMOUNT, EXPENSE_CATEGORY, BUDGET_AMOUNT, BUDGET_CATEGORY, SAVINGS_AMOUNT, SAVINGS_DESCRIPTION = range(6)

# Обновленный список категорий с добавлением "Дети"
CATEGORIES = ['Продукты', 'Транспорт', 'Развлечения', 'Здоровье', 'Одежда', 'Дом', 'Дети', 'Прочее']

# Частота напоминаний
REMINDER_FREQUENCIES = ['Ежедневно', 'Еженедельно', 'Ежемесячно']

PERIOD_LABEL_TO_CODE = {
    'Ежедневно': 'daily',
    'Еженедельно': 'weekly',
    'Ежемесячно': 'monthly'
}
CODE_TO_PERIOD_LABEL = {code: label for label, code in PERIOD_LABEL_TO_CODE.items()}

# Функция для получения основного меню (чтобы не дублировать код)

def is_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли сообщение командой для бота"""
    message = update.message
    
    if not message or not message.text:
        return False
    
    # Если это приватный чат - обрабатываем все сообщения
    if message.chat.type == 'private':
        return True
    
    # В группе обрабатываем только:
    # 1. Команды (начинающиеся с /)
    # 2. Ответы на сообщения бота
    # 3. Сообщения, упоминающие бота
    
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

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        ['/add_expense', '/daily_report'],
        ['/weekly_report', '/monthly_report'],
        ['/detailed_report', '/set_budget'],
        
        ['/my_reminders', '/setname'], ['/web']
    ], resize_keyboard=True)

# Добавление нового расхода
def add_expense(user_id, amount, category):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Получаем имя пользователя из базы
    cursor.execute('SELECT user_name FROM users WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()
    user_name = result['user_name'] if result else "Пользователь"
    
    cursor.execute(
        'INSERT INTO expenses (user_id, amount, category, date, user_name) VALUES (%s, %s, %s, %s, %s)',
        (user_id, amount, category, today, user_name)
    )
    
    conn.commit()
    conn.close()

# Функция для обновления структуры базы данных
# Исправленная функция получения ежедневных расходов
def get_daily_expenses(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute(
        '''SELECT category, SUM(amount) as total
           FROM expenses 
           WHERE date = %s AND user_id = %s
           GROUP BY category
           ORDER BY category''',
        (today, user_id)
    )
    
    results = cursor.fetchall()
    total = sum(float(row['total']) for row in results if row['total'])
    conn.close()
    return results, total

# Получение расходов за неделю
def get_weekly_expenses(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now()
    week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')
    cursor.execute(
        '''SELECT date, SUM(amount) as total 
           FROM expenses 
           WHERE user_id = %s AND date BETWEEN %s AND %s 
           GROUP BY date
           ORDER BY date''',
        (user_id, week_ago, today)
    )
    results = cursor.fetchall()
    total = sum(float(row['total']) for row in results if row['total'])
    conn.close()
    return results, total

# Исправленная функция получения расходов за месяц
def get_monthly_expenses(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now()
    month_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')
    
    try:
        # Добавляем больше логирования
        logging.info(f"Запрос расходов для user_id={user_id} с {month_ago} по {today}")
        
        cursor.execute(
            '''SELECT category, SUM(amount) as total 
               FROM expenses 
               WHERE user_id = %s AND date BETWEEN %s AND %s 
               GROUP BY category
               ORDER BY category''',
            (user_id, month_ago, today)
        )
        results = cursor.fetchall()
        
        # Логируем результаты запроса
        logging.info(f"Получено {len(results)} записей о расходах")
        for i, row in enumerate(results):
            logging.info(f"Запись {i+1}: категория={row['category']}, сумма={row['total']}")
        
        total = sum(row['total'] for row in results)
        logging.info(f"Общая сумма расходов: {total}")
        
        return results, total
    except Exception as e:
        logging.error(f"Ошибка при получении данных о расходах: {e}")
        return [], 0
    finally:
        conn.close()

# Исправленная функция создания графика для месячных расходов
def create_monthly_chart(user_id):
    expenses, _ = get_monthly_expenses(user_id)
    if not expenses:
        logging.warning("Нет данных о расходах для создания графика")
        return None
    
    # Преобразуем строки БД в словари для корректной работы с pandas
    expenses_dict = []
    for expense in expenses:
        total_value = float(expense['total']) if expense['total'] is not None else 0
        expense_dict = {'category': expense['category'], 'total': total_value}
        expenses_dict.append(expense_dict)
    
    logging.info(f"Преобразованные данные для графика: {expenses_dict}")
    
    # Если после преобразования нет данных, возвращаем None
    if not expenses_dict:
        logging.warning("После преобразования нет данных для графика")
        return None
    
    # Создаем DataFrame из списка словарей
    df = pd.DataFrame(expenses_dict)
    
    # Проверяем наличие данных
    if df.empty:
        logging.warning("DataFrame пуст после создания")
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

# Функции для работы с бюджетами
def normalize_period_value(period):
    return PERIOD_LABEL_TO_CODE.get(period, period)


def set_budget(user_id, category, amount, period):
    conn = get_db_connection()
    cursor = conn.cursor()
    start_date = datetime.now().strftime('%Y-%m-%d')
    period_code = normalize_period_value(period)
    
    # Проверяем, существует ли уже бюджет для этой категории и периода
    cursor.execute(
        'SELECT id FROM budgets WHERE user_id = %s AND category = %s AND period = %s',
        (user_id, category, period_code)
    )
    existing_budget = cursor.fetchone()
    
    if existing_budget:
        # Обновляем существующий бюджет
        cursor.execute(
            'UPDATE budgets SET amount = %s, start_date = %s WHERE id = %s',
            (amount, start_date, existing_budget['id'])
        )
    else:
        # Создаем новый бюджет
        cursor.execute(
            'INSERT INTO budgets (user_id, category, amount, period, start_date) VALUES (%s, %s, %s, %s, %s)',
            (user_id, category, amount, period_code, start_date)
        )
    
    conn.commit()
    conn.close()

def get_budgets(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT category, amount, period FROM budgets WHERE user_id = %s',
        (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return results

def check_budget_status(user_id, category, period):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now()
    period_code = normalize_period_value(period)
    
    if period_code == 'daily':
        start_date = today.strftime('%Y-%m-%d')
    elif period_code == 'weekly':
        start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    elif period_code == 'monthly':
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
    else:
        start_date = today.strftime('%Y-%m-%d')
    
    # Получаем бюджет для данной категории
    cursor.execute(
        'SELECT amount FROM budgets WHERE user_id = %s AND category = %s AND period = %s',
        (user_id, category, period_code)
    )
    budget = cursor.fetchone()
    
    if not budget:
        conn.close()
        return None, 0, 0
    
    # Считаем расходы по категории за период
    cursor.execute(
        'SELECT SUM(amount) as spent FROM expenses WHERE user_id = %s AND category = %s AND date >= %s',
        (user_id, category, start_date)
    )
    spent_row = cursor.fetchone()
    spent = float(spent_row['spent']) if spent_row and spent_row['spent'] else 0
    
    # Рассчитываем процент использования бюджета
    budget_amount = float(budget['amount'])
    percentage = (spent / budget_amount) * 100 if budget_amount > 0 else 0
    
    conn.close()
    return budget_amount, spent, percentage

# Функции для работы с целями экономии
def add_savings_goal(user_id, description, target_amount, target_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute(
        'INSERT INTO savings_goals (user_id, description, target_amount, target_date, created_date) VALUES (%s, %s, %s, %s, %s)',
        (user_id, description, target_amount, target_date, created_date)
    )
    
    conn.commit()
    conn.close()

def get_savings_goals(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, description, target_amount, current_amount, target_date FROM savings_goals WHERE user_id = %s',
        (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return results

def update_savings_progress(user_id, goal_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Обновляем текущую сумму цели
    cursor.execute(
        'UPDATE savings_goals SET current_amount = current_amount + %s WHERE id = %s AND user_id = %s',
        (amount, goal_id, user_id)
    )
    
    conn.commit()
    conn.close()

# Функции для работы с напоминаниями
def add_reminder(user_id, message, frequency):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_date = datetime.now().strftime('%Y-%m-%d')
    next_reminder_date = created_date
    
    cursor.execute(
        'INSERT INTO reminders (user_id, message, frequency, next_reminder_date, created_date) VALUES (%s, %s, %s, %s, %s)',
        (user_id, message, frequency, next_reminder_date, created_date)
    )
    
    conn.commit()
    conn.close()

def get_reminders(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, message, frequency, next_reminder_date FROM reminders WHERE user_id = %s',
        (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return results

def delete_reminder(user_id, reminder_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'DELETE FROM reminders WHERE id = %s AND user_id = %s',
        (reminder_id, user_id)
    )
    
    conn.commit()
    conn.close()

def get_todays_reminders():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute(
        'SELECT user_id, id, message, frequency FROM reminders WHERE next_reminder_date <= %s',
        (today,)
    )
    results = cursor.fetchall()
    
    # Обновляем даты следующих напоминаний
    for reminder in results:
        next_date = datetime.now()
        
        if reminder['frequency'] == 'Ежедневно':
            next_date = next_date + timedelta(days=1)
        elif reminder['frequency'] == 'Еженедельно':
            next_date = next_date + timedelta(days=7)
        elif reminder['frequency'] == 'Ежемесячно':
            # Для простоты: добавляем 30 дней для месячных напоминаний
            next_date = next_date + timedelta(days=30)
        
        cursor.execute(
            'UPDATE reminders SET next_reminder_date = %s WHERE id = %s',
            (next_date.strftime('%Y-%m-%d'), reminder['id'])
        )
    
    conn.commit()
    conn.close()
    return results

# Функция проверки превышения бюджета
def check_budget_alerts(user_id, category, amount):
    periods = ['daily', 'weekly', 'monthly']
    alerts = []
    
    for period in periods:
        budget_amount, spent, percentage = check_budget_status(user_id, category, period)
        
        if budget_amount and percentage > 80:
            alerts.append({
                'period': CODE_TO_PERIOD_LABEL.get(period, period),
                'budget': budget_amount,
                'spent': spent,
                'percentage': percentage
            })
    
    return alerts

# Обработка команды старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
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

# Команда для открытия веб-интерфейса
async def web_interface(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

# Начало добавления расхода
async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Введите сумму расхода:')
    return EXPENSE_AMOUNT

# Обработка суммы расхода
async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    try:
        amount = float(user_input)
        context.user_data['amount'] = amount
        
        # Создаем ИНЛАЙН-клавиатуру с категориями (работает в группах)
        keyboard = []
        row = []
        for i, category in enumerate(CATEGORIES):
            row.append(InlineKeyboardButton(category, callback_data=f"category_{category}"))
            if (i + 1) % 3 == 0 or i == len(CATEGORIES) - 1:
                keyboard.append(row)
                row = []
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text('Выберите категорию:', reply_markup=reply_markup)
        return EXPENSE_CATEGORY
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите корректную сумму числом.')
        return EXPENSE_AMOUNT

# Обработчик категории расхода (оставляем для обратной совместимости)
async def expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text
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

# Исправленный обработчик категорий (callback)
async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    
    # Получаем выбранную категорию из callback_data
    category = query.data.replace("category_", "")
    user_id = update.effective_user.id
    amount = context.user_data.get('amount', 0)
    
    # Получаем имя пользователя из контекста или БД
    user_name = context.user_data.get('user_name', None)
    
    if not user_name:
        # Пытаемся получить имя из базы данных
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_name FROM users WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_name = result['user_name']
            # Сохраняем в контекст для будущего использования
            context.user_data['user_name'] = user_name
    
    # Добавляем расход с именем пользователя
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute(
        'INSERT INTO expenses (user_id, amount, category, date, user_name) VALUES (%s, %s, %s, %s, %s)',
        (user_id, amount, category, today, user_name)
    )
    conn.commit()
    conn.close()
    
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

# Исправленная функция отображения ежедневного отчета
async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    expenses, total = get_daily_expenses(user_id)
    
    if not expenses:
        await update.message.reply_text('За сегодня пока нет расходов.', reply_markup=get_main_keyboard())
        return
    
    report = "Расходы за сегодня:\n\n"
    for expense in expenses:
        total_value = float(expense['total']) if expense['total'] else 0
        report += f"{expense['category']}: {total_value:.2f} руб."
        
        # Проверяем наличие ключа user_name перед использованием
        if 'user_name' in expense and expense['user_name']:
            report += f" (добавил: {expense['user_name']})"
        
        report += "\n"
    
    report += f"\nОбщая сумма: {total:.2f} руб."
    await update.message.reply_text(report, reply_markup=get_main_keyboard())

# Еженедельный отчет
async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

# Ежемесячный отчет
async def monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

# Обработчики для бюджетов
async def set_budget_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Создаем клавиатуру с периодами
    keyboard = [[period] for period in ['Ежедневно', 'Еженедельно', 'Ежемесячно']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Установка бюджета. Выберите период:',
        reply_markup=reply_markup
    )
    
    return BUDGET_AMOUNT

async def budget_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    period_label = update.message.text
    period_code = normalize_period_value(period_label)
    context.user_data['budget_period'] = period_code
    context.user_data['budget_period_label'] = CODE_TO_PERIOD_LABEL.get(period_code, period_label)
    
    await update.message.reply_text(f'Выбран период: {period_label}\nВведите сумму бюджета:')
    return BUDGET_CATEGORY

async def budget_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    user_id = update.effective_user.id
    budgets = get_budgets(user_id)
    
    if not budgets:
        await update.message.reply_text('У вас пока нет установленных бюджетов.', reply_markup=get_main_keyboard())
        return
    
    report = "Ваши бюджеты:\n\n"
    
    for budget in budgets:
        category = budget['category']
        amount = float(budget['amount']) if budget['amount'] is not None else 0
        period = budget['period']
        period_label = CODE_TO_PERIOD_LABEL.get(period, period)
        
        _, spent, percentage = check_budget_status(user_id, category, period)
        
        report += f"🔹 {category} ({period_label}): {spent:.2f} / {amount:.2f} руб. ({percentage:.1f}%)\n"
    
    await update.message.reply_text(report, reply_markup=get_main_keyboard())

# Обработчики для целей экономии
async def savings_goal_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Создание цели экономии. Введите описание цели:')
    return SAVINGS_DESCRIPTION

async def savings_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text
    context.user_data['savings_description'] = description
    
    await update.message.reply_text('Введите целевую сумму:')
    return SAVINGS_AMOUNT

async def savings_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    user_id = update.effective_user.id
    goals = get_savings_goals(user_id)
    
    if not goals:
        await update.message.reply_text('У вас пока нет целей экономии.', reply_markup=get_main_keyboard())
        return
    
    report = "Ваши цели экономии:\n\n"
    
    keyboard = []
    for goal in goals:
        description = goal['description']
        target = goal['target_amount']
        current = goal['current_amount'] or 0
        percentage = (current / target) * 100 if target > 0 else 0
        
        report += f"🎯 {description}: {current:.2f} / {target:.2f} руб. ({percentage:.1f}%)\n"
        
        keyboard.append([InlineKeyboardButton(
            f"Пополнить '{description}'",
            callback_data=f"add_to_goal_{goal['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(report, reply_markup=reply_markup)

# Функция для пополнения цели экономии
async def add_to_savings_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

# Функция для обработки колбэков целей экономии
async def process_savings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("add_to_goal_"):
        goal_id = int(query.data.split("_")[-1])
        context.user_data['current_goal_id'] = goal_id
        
        await query.message.reply_text("Введите сумму для пополнения цели:")

# Обработчики для напоминаний
async def set_reminder_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Введите текст напоминания:')
    context.user_data['reminder_stage'] = 'text'

async def process_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    user_id = update.effective_user.id
    reminders = get_reminders(user_id)
    
    if not reminders:
        await update.message.reply_text('У вас пока нет напоминаний.', reply_markup=get_main_keyboard())
        return
    
    report = "Ваши напоминания:\n\n"
    
    keyboard = []
    for reminder in reminders:
        report += f"⏰ {reminder['message']} ({reminder['frequency']})\n"
        keyboard.append([InlineKeyboardButton(
            f"Удалить '{reminder['message'][:20]}..'",
            callback_data=f"del_reminder_{reminder['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(report, reply_markup=reply_markup)

async def process_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("del_reminder_"):
        reminder_id = int(query.data.split("_")[-1])
        user_id = update.effective_user.id
        
        delete_reminder(user_id, reminder_id)
        
        await query.message.reply_text("Напоминание удалено.", reply_markup=get_main_keyboard())

# Отправка ежедневного отчета всем пользователям
async def send_daily_reports(context: ContextTypes.DEFAULT_TYPE) -> None:
    # Получаем список всех пользователей
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT user_id FROM expenses')
    users = cursor.fetchall()
    conn.close()
    
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
                logging.error(f"Ошибка при отправке ежедневного отчета пользователю {user_id}: {e}")

# Проверка и отправка напоминаний
async def check_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    reminders = get_todays_reminders()
    
    for reminder in reminders:
        try:
            await context.bot.send_message(
                chat_id=reminder['user_id'],
                text=f"📣 Напоминание: {reminder['message']}"
            )
        except Exception as e:
            logging.error(f"Ошибка при отправке напоминания: {e}")

# Обработчик общих сообщений
async def handle_general_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик общих сообщений - только для команд боту"""
    
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

# Функция отмены диалога
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Операция отменена.',
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# Обработчик добавления расходов (обновленный)
def create_expense_handler():
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

# Добавляем функцию для установки имени пользователя
async def set_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            'Пожалуйста, укажите ваше имя после команды. Например: /setname Иван',
            reply_markup=get_main_keyboard()
        )
        return
    
    user_name = ' '.join(context.args)
    user_id = update.effective_user.id
    
    # Сохраняем имя пользователя в базе данных или контексте
    context.user_data['user_name'] = user_name
    
    # Также можно сохранить в отдельной таблице для постоянного хранения
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создаем таблицу пользователей, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        user_name TEXT NOT NULL,
        created_date DATE NOT NULL
    )
    ''')
    
    # Проверяем, существует ли уже запись для этого пользователя
    cursor.execute('SELECT user_id FROM users WHERE user_id = %s', (user_id,))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute('UPDATE users SET user_name = %s WHERE user_id = %s', (user_name, user_id))
    else:
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('INSERT INTO users (user_id, user_name, created_date) VALUES (%s, %s, %s)', 
                      (user_id, user_name, today))
    
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f'Ваше имя установлено: {user_name}',
        reply_markup=get_main_keyboard()
    )

# Основная функция

# Функция для детального отчета по пользователям
def get_detailed_monthly_expenses():
    """Получить детальный отчет с разбивкой по пользователям"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now()
    month_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')
    
    cursor.execute(
        '''SELECT user_name, category, SUM(amount) as total 
           FROM expenses 
           WHERE date BETWEEN %s AND %s 
           GROUP BY user_name, category
           ORDER BY user_name, category''',
        (month_ago, today)
    )
    results = cursor.fetchall()
    conn.close()
    return results

async def detailed_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Детальный отчет по пользователям"""
    expenses = get_detailed_monthly_expenses()
    
    if not expenses:
        await update.message.reply_text('За последний месяц нет расходов.', reply_markup=get_main_keyboard())
        return
    
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
    
    await update.message.reply_text(report, reply_markup=get_main_keyboard())

def main() -> None:
    # Ждем готовности базы и инициализируем структуру
    wait_for_db()
    init_db()
    
    # Применение миграций базы данных
    try:
        check_and_update_database()
    except Exception as e:
        logger.error(f"Ошибка при применении миграций: {e}")
        # Fallback на старый метод если новая система миграций не работает
        update_database_structure()
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Уведомление о необходимости установки расширения для очереди заданий
    try:
        job_queue = application.job_queue
        # Если job_queue доступен, настраиваем задания
        job_queue.run_daily(check_reminders, time=time(hour=9, minute=0))
        job_queue.run_daily(send_daily_reports, time=time(hour=21, minute=0))
        logging.info("Очередь заданий успешно настроена.")
    except Exception as e:
        logging.warning(f"Невозможно настроить очередь заданий: {e}")
        logging.warning("Для работы очереди заданий установите расширение: pip install 'python-telegram-bot[job-queue]'")
        logging.warning("Функции напоминаний и автоматических отчетов будут недоступны.")
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("web", web_interface))
    application.add_handler(CommandHandler("daily_report", daily_report))
    application.add_handler(CommandHandler("weekly_report", weekly_report))
    application.add_handler(CommandHandler("monthly_report", monthly_report))
    application.add_handler(CommandHandler("my_budgets", show_budgets))
    application.add_handler(CommandHandler("add_savings_goal", savings_goal_start))
    application.add_handler(CommandHandler("savings_goals", show_savings_goals))
    application.add_handler(CommandHandler("set_reminder", set_reminder_start))
    application.add_handler(CommandHandler("my_reminders", show_reminders))
    
    # Обработчики для inline кнопок
    application.add_handler(CallbackQueryHandler(process_savings_callback, pattern="^add_to_goal_"))
    application.add_handler(CallbackQueryHandler(process_reminder_callback, pattern="^del_reminder_"))
    application.add_handler(CallbackQueryHandler(category_callback, pattern="^category_"))
    
    # Обработчик добавления расходов (обновленный)
    application.add_handler(create_expense_handler())
    
    # Обработчик для установки бюджета
    budget_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_budget", set_budget_start)],
        states={
            BUDGET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_amount)],
            BUDGET_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_category)],
            BUDGET_CATEGORY + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_budget)],
        },
        fallbacks=[],
    )
    application.add_handler(budget_conv_handler)
    
    # Обработчик для создания цели экономии
    savings_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_savings_goal", savings_goal_start)],
        states={
            SAVINGS_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, savings_description)],
            SAVINGS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, savings_amount)],
        },
        fallbacks=[],
    )
    application.add_handler(savings_conv_handler)
    
    # Обработчик общих сообщений (для напоминаний и пополнения целей)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_general_messages
    ))
    
    # Добавляем обработчик для установки имени пользователя
    application.add_handler(CommandHandler("setname", set_username))
    application.add_handler(CommandHandler("detailed_report", detailed_monthly_report))
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
