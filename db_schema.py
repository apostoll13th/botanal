import logging
from db import get_db_connection

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database schema with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    logger.info("Creating expenses table if not exists...")
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

    logger.info("Creating budgets table if not exists...")
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

    logger.info("Creating savings_goals table if not exists...")
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

    logger.info("Creating reminders table if not exists...")
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

    logger.info("Creating users table if not exists...")
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
    logger.info("Database schema initialization completed")


def update_database_structure():
    """Legacy method to update database structure (use migrations instead)"""
    logger.info("Running legacy database structure update...")
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
            logger.info("Adding column %s to table %s", column, table)
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

    try:
        ensure_column("expenses", "user_name", "TEXT")
        ensure_column("expenses", "description", "TEXT")
        ensure_column("budgets", "user_name", "TEXT")
        ensure_column("savings_goals", "user_name", "TEXT")
        ensure_column("savings_goals", "goal_name", "TEXT")
        conn.commit()
        logger.info("Legacy database structure update completed")
    except Exception as e:
        logger.error(f"Error updating database structure: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
