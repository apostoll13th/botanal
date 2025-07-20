from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os
import sys

# Добавляем путь к родительской директории для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Путь к базе данных
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'expenses.db')

def get_db_connection():
    """Подключение к базе данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
        query = 'SELECT * FROM expenses WHERE user_id = ?'
        params = [user_id]
        
        # Добавляем фильтры
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        
        # Преобразуем в список словарей
        result = []
        for expense in expenses:
            result.append({
                'id': expense['id'],
                'amount': expense['amount'],
                'category': expense['category'],
                'date': expense['date'],
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
            WHERE user_id = ? AND date >= ?
            GROUP BY category
            ORDER BY total DESC
        ''', (user_id, date_30_days_ago))
        
        summary = cursor.fetchall()
        
        result = {
            'categories': [],
            'total': 0
        }
        
        for row in summary:
            result['categories'].append({
                'category': row['category'],
                'amount': row['total']
            })
            result['total'] += row['total']
        
        # Добавляем расходы по дням для графика динамики
        cursor.execute('''
            SELECT date, SUM(amount) as daily_total
            FROM expenses
            WHERE user_id = ? AND date >= ?
            GROUP BY date
            ORDER BY date
        ''', (user_id, date_30_days_ago))
        
        daily_expenses = cursor.fetchall()
        
        result['daily'] = []
        for row in daily_expenses:
            result['daily'].append({
                'date': row['date'],
                'amount': row['daily_total']
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
            WHERE user_id = ?
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
                WHERE user_id = ? AND category = ? AND date >= ?
            ''', (user_id, budget['category'], period_start.strftime('%Y-%m-%d')))
            
            spent_row = cursor.fetchone()
            spent = spent_row['spent'] if spent_row['spent'] else 0
            
            result.append({
                'id': budget['id'],
                'category': budget['category'],
                'amount': budget['amount'],
                'period': budget['period'],
                'spent': spent,
                'remaining': budget['amount'] - spent,
                'percentage': round((spent / budget['amount']) * 100, 1) if budget['amount'] > 0 else 0
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
            WHERE user_id = ?
            ORDER BY created_date DESC
        ''', (user_id,))
        
        goals = cursor.fetchall()
        
        result = []
        for goal in goals:
            goal_name = goal['goal_name'] if 'goal_name' in goal.keys() else goal['description']
            result.append({
                'id': goal['id'],
                'name': goal_name,
                'description': goal['description'],
                'target_amount': goal['target_amount'],
                'current_amount': goal['current_amount'],
                'target_date': goal['target_date'] if 'target_date' in goal.keys() else None,
                'created_date': goal['created_date'],
                'percentage': round((goal['current_amount'] / goal['target_amount']) * 100, 1) if goal['target_amount'] > 0 else 0
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
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            result = {
                'user_id': user['user_id'],
                'user_name': user['user_name'],
                'created_date': user['created_date']
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