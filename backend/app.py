from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta, date
from decimal import Decimal
import os
import sys

# Добавляем путь к родительской директории для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db_connection, wait_for_db
from db_schema import init_db, update_database_structure
from database_migrations import check_and_update_database

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

try:
    wait_for_db()
    init_db()
    update_database_structure()
    check_and_update_database()
except Exception as exc:
    app.logger.warning("Не удалось применить миграции при старте backend: %s", exc)


def to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def format_date_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({'status': 'ok'})

@app.route('/api/expenses/<int:user_id>', methods=['GET'])
def get_expenses(user_id):
    """Получить все расходы пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем параметры фильтрации
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        
        # Базовый запрос
        query = 'SELECT * FROM expenses WHERE user_id = %s'
        params = [user_id]
        
        # Добавляем фильтры
        if start_date:
            query += ' AND date >= %s'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= %s'
            params.append(end_date)
        
        if category:
            query += ' AND category = %s'
            params.append(category)
        
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        
        # Преобразуем в список словарей
        result = []
        for expense in expenses:
            result.append({
                'id': expense['id'],
                'amount': to_float(expense['amount']),
                'category': expense['category'],
                'date': format_date_value(expense['date']),
                'description': expense['description'] if 'description' in expense.keys() else None,
                'user_name': expense['user_name'] if 'user_name' in expense.keys() else None
            })
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses-summary/<int:user_id>', methods=['GET'])
def get_expenses_summary(user_id):
    """Получить агрегированные расходы по категориям за последние 30 дней"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Дата 30 дней назад
        date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Агрегированные расходы по категориям
        cursor.execute('''
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = %s AND date >= %s
            GROUP BY category
            ORDER BY total DESC
        ''', (user_id, date_30_days_ago))
        
        summary = cursor.fetchall()
        
        result = {
            'categories': [],
            'total': 0
        }
        
        for row in summary:
            amount = to_float(row['total'])
            if amount is None:
                amount = 0
            result['categories'].append({
                'category': row['category'],
                'amount': amount
            })
            result['total'] += amount
        
        # Добавляем расходы по дням для графика динамики
        cursor.execute('''
            SELECT date, SUM(amount) as daily_total
            FROM expenses
            WHERE user_id = %s AND date >= %s
            GROUP BY date
            ORDER BY date
        ''', (user_id, date_30_days_ago))
        
        daily_expenses = cursor.fetchall()
        
        result['daily'] = []
        for row in daily_expenses:
            daily_total = to_float(row['daily_total'])
            if daily_total is None:
                daily_total = 0
            result['daily'].append({
                'date': format_date_value(row['date']),
                'amount': daily_total
            })
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets/<int:user_id>', methods=['GET'])
def get_budgets(user_id):
    """Получить бюджеты пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM budgets
            WHERE user_id = %s
            ORDER BY category
        ''', (user_id,))
        
        budgets = cursor.fetchall()
        
        result = []
        for budget in budgets:
            # Считаем текущие расходы по категории
            period_start = datetime.now()
            
            if budget['period'] == 'daily':
                period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            elif budget['period'] == 'weekly':
                period_start = period_start - timedelta(days=period_start.weekday())
                period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            elif budget['period'] == 'monthly':
                period_start = period_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            cursor.execute('''
                SELECT SUM(amount) as spent
                FROM expenses
                WHERE user_id = %s AND category = %s AND date >= %s
            ''', (user_id, budget['category'], period_start.strftime('%Y-%m-%d')))
            
            spent_row = cursor.fetchone()
            spent = to_float(spent_row['spent']) if spent_row and spent_row['spent'] else 0
            amount_value = to_float(budget['amount']) if budget['amount'] is not None else 0
            
            result.append({
                'id': budget['id'],
                'category': budget['category'],
                'amount': amount_value,
                'period': budget['period'],
                'spent': spent,
                'remaining': amount_value - spent,
                'percentage': round((spent / amount_value) * 100, 1) if amount_value > 0 else 0
            })
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/goals/<int:user_id>', methods=['GET'])
def get_goals(user_id):
    """Получить цели накоплений пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM savings_goals
            WHERE user_id = %s
            ORDER BY created_date DESC
        ''', (user_id,))
        
        goals = cursor.fetchall()
        
        result = []
        for goal in goals:
            target_amount = to_float(goal['target_amount']) if goal['target_amount'] is not None else 0
            current_amount = to_float(goal['current_amount']) if goal['current_amount'] is not None else 0
            goal_name = goal['goal_name'] if 'goal_name' in goal.keys() else goal['description']
            result.append({
                'id': goal['id'],
                'name': goal_name,
                'description': goal['description'],
                'target_amount': target_amount,
                'current_amount': current_amount,
                'target_date': format_date_value(goal['target_date']) if 'target_date' in goal.keys() else None,
                'created_date': format_date_value(goal['created_date']),
                'percentage': round((current_amount / target_amount) * 100, 1) if target_amount > 0 else 0
            })
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    """Получить информацию о пользователе"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        
        if user:
            result = {
                'user_id': user['user_id'],
                'user_name': user['user_name'],
                'created_date': format_date_value(user['created_date'])
            }
        else:
            result = {
                'user_id': user_id,
                'user_name': 'Пользователь',
                'created_date': None
            }
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Проверяем наличие базы данных
    if not os.path.exists(DB_PATH):
        print(f"База данных не найдена: {DB_PATH}")
        sys.exit(1)
    
    # Запускаем сервер
    app.run(debug=True, host='0.0.0.0', port=5000)
