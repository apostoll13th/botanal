Я вижу проблему с ошибкой `sqlite3.OperationalError: no such column: user_name`. Эта ошибка возникает потому, что функция `get_daily_expenses` пытается обратиться к колонке `user_name`, которая еще не была добавлена в таблицу расходов.

Вот более правильный порядок действий, чтобы исправить эту проблему:

1. Сначала нужно изменить базу данных, добавив новое поле
2. Затем можно использовать это поле в запросах

Давайте создадим функцию для обновления структуры базы данных:

```python
def update_database_structure():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем, существует ли колонка user_name в таблице expenses
    try:
        cursor.execute('SELECT user_name FROM expenses LIMIT 1')
        logging.info("Колонка user_name уже существует в таблице expenses")
    except sqlite3.OperationalError:
        # Колонка не существует, добавляем её
        logging.info("Добавление колонки user_name в таблицу expenses")
        cursor.execute('ALTER TABLE expenses ADD COLUMN user_name TEXT')
        conn.commit()
    
    conn.close()
```

Затем вызовите эту функцию в начале функции `main()` перед созданием обработчиков:

```python
def main() -> None:
    # Инициализация базы данных
    init_db()
    
    # Обновление структуры базы данных для добавления новых полей
    update_database_structure()
    
    # ... остальной код ...
```

А функцию `get_daily_expenses` нужно модифицировать, чтобы она работала правильно даже если колонка `user_name` отсутствует:

```python
def get_daily_expenses(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Проверяем, существует ли колонка user_name
    try:
        # Получаем все расходы за сегодня (независимо от пользователя)
        cursor.execute(
            '''SELECT category, SUM(amount) as total, user_name
               FROM expenses 
               WHERE date = ? 
               GROUP BY category''',
            (today,)
        )
    except sqlite3.OperationalError:
        # Если колонки user_name нет, используем запрос без неё
        cursor.execute(
            '''SELECT category, SUM(amount) as total
               FROM expenses 
               WHERE date = ? 
               GROUP BY category''',
            (today,)
        )
    
    results = cursor.fetchall()
    total = sum(row['total'] for row in results)
    conn.close()
    return results, total
```

Это решение позволит боту работать корректно, даже если структура базы данных еще не обновлена.

Дополнительно, в функции `daily_report` нужно проверять наличие ключа `user_name` в каждой записи:

```python
async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    expenses, total = get_daily_expenses(user_id)
    
    if not expenses:
        await update.message.reply_text('За сегодня пока нет расходов.', reply_markup=get_main_keyboard())
        return
    
    report = "Расходы за сегодня:\n\n"
    for expense in expenses:
        report += f"{expense['category']}: {expense['total']} руб."
        
        # Проверяем наличие ключа user_name перед использованием
        if 'user_name' in expense and expense['user_name']:
            report += f" (добавил: {expense['user_name']})"
        
        report += "\n"
    
    report += f"\nОбщая сумма: {total} руб."
    await update.message.reply_text(report, reply_markup=get_main_keyboard())
```

После внесения этих изменений ваш бот должен заработать корректно с общей базой данных для вас и вашей жены.