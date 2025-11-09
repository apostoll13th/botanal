"""
Database operations for the expense tracking bot.
Contains all functions for working with expenses, budgets, savings goals, and reminders.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

import bcrypt
import psycopg2
from psycopg2 import IntegrityError

from db import get_db_connection
from config import PERIOD_LABEL_TO_CODE, CODE_TO_PERIOD_LABEL, Config, CATEGORIES

logger = logging.getLogger(__name__)


def normalize_period_value(period: str) -> str:
    """Normalize period value from label to code"""
    return PERIOD_LABEL_TO_CODE.get(period, period)


# ========== EXPENSE OPERATIONS ==========

def add_expense(user_id: int, amount: float, category: str) -> None:
    """Add a new expense for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        # Получаем имя пользователя из базы
        cursor.execute('SELECT user_name FROM users WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        user_name = result['user_name'] if result else "Пользователь"

        cursor.execute(
            'INSERT INTO expenses (user_id, amount, category, date, user_name) VALUES (%s, %s, %s, %s, %s)',
            (user_id, amount, category, today, user_name)
        )

        conn.commit()
        logger.info(f"Expense added: user_id={user_id}, amount={amount}, category={category}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding expense: {e}")
        raise
    finally:
        conn.close()


def get_recent_expenses(user_id: int, limit: int = 5) -> List[Dict]:
    """Get recent expenses for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            '''SELECT id, amount, category, date, description, transaction_type
               FROM expenses
               WHERE user_id = %s
               ORDER BY date DESC, id DESC
               LIMIT %s''',
            (user_id, limit)
        )
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error getting recent expenses: {e}")
        return []
    finally:
        conn.close()


def delete_expense(user_id: int, expense_id: int) -> bool:
    """Delete an expense by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Проверяем, что операция принадлежит пользователю
        cursor.execute(
            'SELECT user_id FROM expenses WHERE id = %s',
            (expense_id,)
        )
        result = cursor.fetchone()

        if not result:
            logger.warning(f"Expense {expense_id} not found")
            return False

        if result['user_id'] != user_id:
            logger.warning(f"User {user_id} trying to delete expense {expense_id} of another user")
            return False

        cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
        conn.commit()
        logger.info(f"Expense deleted: id={expense_id}, user_id={user_id}")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting expense: {e}")
        raise
    finally:
        conn.close()


def get_daily_expenses(user_id: int) -> Tuple[List[Dict], float]:
    """Get today's expenses for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')

    try:
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
        return results, total
    except Exception as e:
        logger.error(f"Error getting daily expenses: {e}")
        return [], 0
    finally:
        conn.close()


def get_weekly_expenses(user_id: int) -> Tuple[List[Dict], float]:
    """Get weekly expenses for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now()
    week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    try:
        cursor.execute(
            '''SELECT date, SUM(amount) as total
               FROM expenses
               WHERE user_id = %s AND date BETWEEN %s AND %s
               GROUP BY date
               ORDER BY date''',
            (user_id, week_ago, today_str)
        )
        results = cursor.fetchall()
        total = sum(float(row['total']) for row in results if row['total'])
        return results, total
    except Exception as e:
        logger.error(f"Error getting weekly expenses: {e}")
        return [], 0
    finally:
        conn.close()


def get_monthly_expenses(user_id: int) -> Tuple[List[Dict], float]:
    """Get monthly expenses for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now()
    month_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    try:
        logger.info(f"Getting expenses for user_id={user_id} from {month_ago} to {today_str}")

        cursor.execute(
            '''SELECT category, SUM(amount) as total
               FROM expenses
               WHERE user_id = %s AND date BETWEEN %s AND %s
               GROUP BY category
               ORDER BY category''',
            (user_id, month_ago, today_str)
        )
        results = cursor.fetchall()

        logger.info(f"Got {len(results)} expense records")
        for i, row in enumerate(results):
            logger.info(f"Record {i+1}: category={row['category']}, total={row['total']}")

        total = sum(row['total'] for row in results)
        logger.info(f"Total expenses: {total}")

        return results, total
    except Exception as e:
        logger.error(f"Error getting monthly expenses: {e}")
        return [], 0
    finally:
        conn.close()


def get_detailed_monthly_expenses() -> List[Dict]:
    """Get detailed monthly report with breakdown by users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now()
    month_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    try:
        cursor.execute(
            '''SELECT user_name, category, SUM(amount) as total
               FROM expenses
               WHERE date BETWEEN %s AND %s
               GROUP BY user_name, category
               ORDER BY user_name, category''',
            (month_ago, today_str)
        )
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error getting detailed monthly expenses: {e}")
        return []
    finally:
        conn.close()


# ========== BUDGET OPERATIONS ==========

def set_budget(user_id: int, category: str, amount: float, period: str) -> None:
    """Set or update a budget for a category and period"""
    conn = get_db_connection()
    cursor = conn.cursor()
    start_date = datetime.now().strftime('%Y-%m-%d')
    period_code = normalize_period_value(period)

    try:
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
            logger.info(f"Budget updated: user_id={user_id}, category={category}, period={period_code}")
        else:
            # Создаем новый бюджет
            cursor.execute(
                'INSERT INTO budgets (user_id, category, amount, period, start_date) VALUES (%s, %s, %s, %s, %s)',
                (user_id, category, amount, period_code, start_date)
            )
            logger.info(f"Budget created: user_id={user_id}, category={category}, period={period_code}")

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error setting budget: {e}")
        raise
    finally:
        conn.close()


def get_budgets(user_id: int) -> List[Dict]:
    """Get all budgets for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT category, amount, period FROM budgets WHERE user_id = %s',
            (user_id,)
        )
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error getting budgets: {e}")
        return []
    finally:
        conn.close()


def check_budget_status(user_id: int, category: str, period: str) -> Tuple[Optional[float], float, float]:
    """Check budget status for a category and period"""
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now()
    period_code = normalize_period_value(period)

    # Определяем дату начала периода
    if period_code == 'daily':
        start_date = today.strftime('%Y-%m-%d')
    elif period_code == 'weekly':
        start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    elif period_code == 'monthly':
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
    else:
        start_date = today.strftime('%Y-%m-%d')

    try:
        # Получаем бюджет для данной категории
        cursor.execute(
            'SELECT amount FROM budgets WHERE user_id = %s AND category = %s AND period = %s',
            (user_id, category, period_code)
        )
        budget = cursor.fetchone()

        if not budget:
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

        return budget_amount, spent, percentage
    except Exception as e:
        logger.error(f"Error checking budget status: {e}")
        return None, 0, 0
    finally:
        conn.close()


def check_budget_alerts(user_id: int, category: str, amount: float) -> List[Dict]:
    """Check for budget alerts across all periods"""
    periods = ['daily', 'weekly', 'monthly']
    alerts = []

    for period in periods:
        budget_amount, spent, percentage = check_budget_status(user_id, category, period)

        if budget_amount and percentage > Config.BUDGET_ALERT_THRESHOLD:
            alerts.append({
                'period': CODE_TO_PERIOD_LABEL.get(period, period),
                'budget': budget_amount,
                'spent': spent,
                'percentage': percentage
            })

    return alerts


# ========== SAVINGS GOAL OPERATIONS ==========

def add_savings_goal(user_id: int, description: str, target_amount: float, target_date: Optional[str] = None) -> None:
    """Add a new savings goal"""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_date = datetime.now().strftime('%Y-%m-%d')

    try:
        cursor.execute(
            'INSERT INTO savings_goals (user_id, description, target_amount, target_date, created_date) VALUES (%s, %s, %s, %s, %s)',
            (user_id, description, target_amount, target_date, created_date)
        )

        conn.commit()
        logger.info(f"Savings goal added: user_id={user_id}, description={description}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding savings goal: {e}")
        raise
    finally:
        conn.close()


def get_savings_goals(user_id: int) -> List[Dict]:
    """Get all savings goals for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT id, description, target_amount, current_amount, target_date FROM savings_goals WHERE user_id = %s',
            (user_id,)
        )
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error getting savings goals: {e}")
        return []
    finally:
        conn.close()


def update_savings_progress(user_id: int, goal_id: int, amount: float) -> None:
    """Update progress on a savings goal"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Обновляем текущую сумму цели
        cursor.execute(
            'UPDATE savings_goals SET current_amount = current_amount + %s WHERE id = %s AND user_id = %s',
            (amount, goal_id, user_id)
        )

        conn.commit()
        logger.info(f"Savings goal updated: goal_id={goal_id}, amount={amount}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating savings goal: {e}")
        raise
    finally:
        conn.close()


# ========== REMINDER OPERATIONS ==========

def add_reminder(user_id: int, message: str, frequency: str) -> None:
    """Add a new reminder"""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_date = datetime.now().strftime('%Y-%m-%d')
    next_reminder_date = created_date

    try:
        cursor.execute(
            'INSERT INTO reminders (user_id, message, frequency, next_reminder_date, created_date) VALUES (%s, %s, %s, %s, %s)',
            (user_id, message, frequency, next_reminder_date, created_date)
        )

        conn.commit()
        logger.info(f"Reminder added: user_id={user_id}, frequency={frequency}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding reminder: {e}")
        raise
    finally:
        conn.close()


def get_reminders(user_id: int) -> List[Dict]:
    """Get all reminders for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT id, message, frequency, next_reminder_date FROM reminders WHERE user_id = %s',
            (user_id,)
        )
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error getting reminders: {e}")
        return []
    finally:
        conn.close()


def delete_reminder(user_id: int, reminder_id: int) -> None:
    """Delete a reminder"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'DELETE FROM reminders WHERE id = %s AND user_id = %s',
            (reminder_id, user_id)
        )

        conn.commit()
        logger.info(f"Reminder deleted: reminder_id={reminder_id}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting reminder: {e}")
        raise
    finally:
        conn.close()


def get_todays_reminders() -> List[Dict]:
    """Get all reminders that need to be sent today"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')

    try:
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
        return results
    except Exception as e:
        logger.error(f"Error getting today's reminders: {e}")
        return []
    finally:
        conn.close()


# ========== USER OPERATIONS ==========

def save_user(user_id: int, user_name: str) -> None:
    """Save or update user information"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Проверяем, существует ли уже запись для этого пользователя
        cursor.execute('SELECT user_id FROM users WHERE user_id = %s', (user_id,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute('UPDATE users SET user_name = %s WHERE user_id = %s', (user_name, user_id))
            logger.info(f"User updated: user_id={user_id}, user_name={user_name}")
        else:
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('INSERT INTO users (user_id, user_name, created_date) VALUES (%s, %s, %s)',
                          (user_id, user_name, today))
            logger.info(f"User created: user_id={user_id}, user_name={user_name}")

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving user: {e}")
        raise
    finally:
        conn.close()


def get_user_name(user_id: int) -> Optional[str]:
    """Get user name from database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT user_name FROM users WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        return result['user_name'] if result else None
    except Exception as e:
        logger.error(f"Error getting user name: {e}")
        return None
    finally:
        conn.close()


def get_all_users() -> List[Dict]:
    """Get all users who have expenses"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT DISTINCT user_id FROM expenses')
        users = cursor.fetchall()
        return users
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []
    finally:
        conn.close()
# ========== CATEGORY OPERATIONS ==========

def get_available_categories() -> List[str]:
    """Return list of categories from DB or fallback to defaults"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM categories ORDER BY name")
        rows = cursor.fetchall()
        categories = [row["name"] for row in rows if row.get("name")]
        if categories:
            return categories
    except Exception as e:
        logger.warning(f"Error fetching categories from DB: {e}")
    finally:
        conn.close()
    return CATEGORIES


# ========== PORTAL ACCOUNTS ==========

def get_app_user_by_telegram_id(user_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, login, role, full_name
            FROM app_users
            WHERE telegram_user_id = %s
            """,
            (user_id,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def create_portal_user(login: str, password: str, telegram_user_id: int, full_name: str = "", role: str = "analyst") -> None:
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Синхронизируем таблицу users
        user_display_name = full_name if full_name else "Пользователь"
        cursor.execute(
            """
            INSERT INTO users (user_id, user_name, created_date)
            VALUES (%s, %s, CURRENT_DATE)
            ON CONFLICT (user_id) DO UPDATE SET user_name = EXCLUDED.user_name
            """,
            (telegram_user_id, user_display_name)
        )

        # Создаем app_users
        cursor.execute(
            """
            INSERT INTO app_users (login, password_hash, full_name, role, telegram_user_id)
            VALUES (%s, %s, NULLIF(%s, ''), %s, %s)
            """,
            (login, password_hash, full_name or "", role, telegram_user_id),
        )
        conn.commit()
        logger.info(f"Portal user created: login={login}, telegram_user_id={telegram_user_id}")
    except IntegrityError as exc:
        conn.rollback()
        logger.error(f"Error creating portal user: {exc}")
        raise ValueError("Login already exists") from exc
    finally:
        conn.close()


def reset_app_user_password(telegram_user_id: int, new_password: str) -> Optional[str]:
    password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE app_users
            SET password_hash = %s
            WHERE telegram_user_id = %s
            RETURNING login, full_name
            """,
            (password_hash, telegram_user_id),
        )
        result = cursor.fetchone()
        if result:
            # Синхронизируем таблицу users при сбросе пароля
            user_display_name = result['full_name'] if result.get('full_name') else "Пользователь"
            cursor.execute(
                """
                INSERT INTO users (user_id, user_name, created_date)
                VALUES (%s, %s, CURRENT_DATE)
                ON CONFLICT (user_id) DO UPDATE SET user_name = EXCLUDED.user_name
                """,
                (telegram_user_id, user_display_name)
            )
            conn.commit()
            logger.info(f"Password reset for telegram_user_id={telegram_user_id}, login={result['login']}")
            return result["login"]
        conn.rollback()
        logger.warning(f"No app_user found for telegram_user_id={telegram_user_id}")
        return None
    except psycopg2.Error as exc:
        conn.rollback()
        logger.error(f"Error resetting password: {exc}")
        return None
    finally:
        conn.close()
