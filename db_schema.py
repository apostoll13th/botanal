import logging
from db import get_db_connection


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            category TEXT NOT NULL,
            date DATE NOT NULL,
            user_name TEXT,
            description TEXT
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            category TEXT NOT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            period TEXT NOT NULL,
            start_date DATE NOT NULL,
            user_name TEXT
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS savings_goals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            description TEXT NOT NULL,
            target_amount NUMERIC(12, 2) NOT NULL,
            current_amount NUMERIC(12, 2) DEFAULT 0,
            target_date DATE,
            created_date DATE NOT NULL,
            goal_name TEXT,
            user_name TEXT
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            frequency TEXT NOT NULL,
            next_reminder_date DATE NOT NULL,
            created_date DATE NOT NULL
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            user_name TEXT NOT NULL,
            created_date DATE NOT NULL
        )
        '''
    )

    conn.commit()
    conn.close()


def update_database_structure():
    conn = get_db_connection()
    cursor = conn.cursor()

    def ensure_column(table, column, ddl):
        cursor.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        if cursor.fetchone() is None:
            logging.info("Добавление колонки %s в таблицу %s", column, table)
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

    try:
        ensure_column("expenses", "user_name", "TEXT")
        ensure_column("expenses", "description", "TEXT")
        ensure_column("budgets", "user_name", "TEXT")
        ensure_column("savings_goals", "user_name", "TEXT")
        ensure_column("savings_goals", "goal_name", "TEXT")
        conn.commit()
    finally:
        conn.close()
