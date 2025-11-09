import logging
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from db import get_database_url, wait_for_db

logger = logging.getLogger(__name__)


class DatabaseMigration:
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or get_database_url()

    def get_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def init_migration_table(self):
        """Создание таблицы для отслеживания миграций"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                version INTEGER UNIQUE NOT NULL,
                description TEXT,
                applied_at TIMESTAMP NOT NULL
            )
            """
        )

        conn.commit()
        conn.close()

    def get_current_version(self):
        """Получение текущей версии БД"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COALESCE(MAX(version), 0) as version FROM migrations")
        result = cursor.fetchone()
        version = result["version"] if result else 0

        conn.close()
        return version

    def column_exists(self, table_name, column_name):
        """Проверка существования колонки в таблице"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
            """,
            (table_name, column_name),
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def apply_migration(self, version, description, migration_func):
        """Применение миграции"""
        current_version = self.get_current_version()

        if version <= current_version:
            logger.info("Миграция %s уже применена", version)
            return

        logger.info("Применение миграции %s: %s", version, description)

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            migration_func(cursor)

            cursor.execute(
                """
                INSERT INTO migrations (version, description, applied_at)
                VALUES (%s, %s, %s)
                """,
                (version, description, datetime.now()),
            )

            conn.commit()
            logger.info("Миграция %s успешно применена", version)

        except Exception as e:
            conn.rollback()
            logger.error("Ошибка при применении миграции %s: %s", version, e)
            raise
        finally:
            conn.close()

    def run_migrations(self):
        """Запуск всех миграций"""
        self.init_migration_table()

        def migration_1(cursor):
            if not self.column_exists("expenses", "user_name"):
                cursor.execute("ALTER TABLE expenses ADD COLUMN user_name TEXT")
                logger.info("Добавлена колонка user_name в таблицу expenses")

        def migration_2(cursor):
            if not self.column_exists("budgets", "user_name"):
                cursor.execute("ALTER TABLE budgets ADD COLUMN user_name TEXT")
                logger.info("Добавлена колонка user_name в таблицу budgets")

        def migration_3(cursor):
            if not self.column_exists("savings_goals", "user_name"):
                cursor.execute("ALTER TABLE savings_goals ADD COLUMN user_name TEXT")
                logger.info("Добавлена колонка user_name в таблицу savings_goals")

        def migration_4(cursor):
            if not self.column_exists("expenses", "description"):
                cursor.execute("ALTER TABLE expenses ADD COLUMN description TEXT")
                logger.info("Добавлена колонка description в таблицу expenses")

        def migration_5(cursor):
            if not self.column_exists("savings_goals", "goal_name"):
                cursor.execute("ALTER TABLE savings_goals ADD COLUMN goal_name TEXT")
                logger.info("Добавлена колонка goal_name в таблицу savings_goals")

        migrations = [
            (1, "Добавление user_name в expenses", migration_1),
            (2, "Добавление user_name в budgets", migration_2),
            (3, "Добавление user_name в savings_goals", migration_3),
            (4, "Добавление description в expenses", migration_4),
            (5, "Добавление goal_name в savings_goals", migration_5),
        ]

        for version, description, func in migrations:
            try:
                self.apply_migration(version, description, func)
            except Exception as e:
                logger.error("Ошибка при применении миграции %s: %s", version, e)


def check_and_update_database():
    """Функция для проверки и обновления структуры БД"""
    wait_for_db()
    migration = DatabaseMigration()
    migration.run_migrations()
    logger.info("Проверка и обновление базы данных завершены")
