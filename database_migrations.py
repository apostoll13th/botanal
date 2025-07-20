import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseMigration:
    def __init__(self, db_path='expenses.db'):
        self.db_path = db_path
        
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_migration_table(self):
        """Создание таблицы для отслеживания миграций"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY,
            version INTEGER UNIQUE NOT NULL,
            description TEXT,
            applied_at TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_current_version(self):
        """Получение текущей версии БД"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT MAX(version) as version FROM migrations')
            result = cursor.fetchone()
            version = result['version'] if result['version'] else 0
        except sqlite3.OperationalError:
            version = 0
            
        conn.close()
        return version
    
    def apply_migration(self, version, description, migration_func):
        """Применение миграции"""
        current_version = self.get_current_version()
        
        if version <= current_version:
            logger.info(f"Миграция {version} уже применена")
            return
            
        logger.info(f"Применение миграции {version}: {description}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Выполняем миграцию
            migration_func(cursor)
            
            # Записываем информацию о миграции
            cursor.execute('''
            INSERT INTO migrations (version, description, applied_at) 
            VALUES (?, ?, ?)
            ''', (version, description, datetime.now().isoformat()))
            
            conn.commit()
            logger.info(f"Миграция {version} успешно применена")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка при применении миграции {version}: {e}")
            raise
        finally:
            conn.close()
    
    def run_migrations(self):
        """Запуск всех миграций"""
        self.init_migration_table()
        
        # Миграция 1: Добавление user_name в expenses
        def migration_1(cursor):
            cursor.execute('''
            ALTER TABLE expenses ADD COLUMN user_name TEXT
            ''')
            
        # Миграция 2: Добавление user_name в budgets
        def migration_2(cursor):
            cursor.execute('''
            ALTER TABLE budgets ADD COLUMN user_name TEXT
            ''')
            
        # Миграция 3: Добавление user_name в savings_goals
        def migration_3(cursor):
            cursor.execute('''
            ALTER TABLE savings_goals ADD COLUMN user_name TEXT
            ''')
            
        # Миграция 4: Добавление description в expenses
        def migration_4(cursor):
            cursor.execute('''
            ALTER TABLE expenses ADD COLUMN description TEXT
            ''')
            
        # Миграция 5: Добавление goal_name в savings_goals
        def migration_5(cursor):
            cursor.execute('''
            ALTER TABLE savings_goals ADD COLUMN goal_name TEXT
            ''')
            
        # Применяем миграции
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
            except sqlite3.OperationalError as e:
                # Если колонка уже существует, пропускаем
                if "duplicate column name" in str(e).lower():
                    logger.info(f"Колонка из миграции {version} уже существует, пропускаем")
                else:
                    raise

def check_and_update_database():
    """Функция для проверки и обновления структуры БД"""
    migration = DatabaseMigration()
    migration.run_migrations()
    logger.info("Проверка и обновление базы данных завершены")