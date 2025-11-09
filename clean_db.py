#!/usr/bin/env python3
"""
Скрипт для очистки базы данных бота (PostgreSQL).
ВНИМАНИЕ: Это действие необратимо!
"""

from contextlib import contextmanager
from typing import Iterable

import psycopg2

from db import get_database_url, wait_for_db

TABLES = ['expenses', 'budgets', 'savings_goals', 'reminders', 'users']


@contextmanager
def get_connection():
    conn = psycopg2.connect(get_database_url())
    try:
        yield conn
    finally:
        conn.close()


def show_database_stats():
    """Показывает количество записей в основных таблицах"""
    with get_connection() as conn:
        cursor = conn.cursor()
        print("\n📊 Статистика базы данных:")
        print("-" * 40)
        for table in TABLES:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"{table:15}: {count:5} записей")


def truncate_tables(tables: Iterable[str]):
    """Очистка таблиц с сбросом последовательностей"""
    with get_connection() as conn:
        cursor = conn.cursor()
        table_list = ', '.join(tables)
        cursor.execute(f'TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE')
        conn.commit()
        print(f"✅ Таблицы {table_list} очищены")


def clear_specific_table(table_name: str):
    truncate_tables([table_name])


def clear_all_tables():
    truncate_tables(TABLES)


def clear_user_data(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        for table in TABLES:
            if table == 'users':
                cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
            else:
                cursor.execute(f'DELETE FROM {table} WHERE user_id = %s', (user_id,))
        conn.commit()
        print(f"✅ Все данные пользователя {user_id} удалены")


def main():
    print("🗄️  Утилита очистки базы данных бота")
    print("=" * 50)

    wait_for_db()
    show_database_stats()

    menu = """
Выберите действие:
1. Очистить все таблицы (полная очистка)
2. Очистить только расходы (expenses)
3. Очистить только бюджеты (budgets)
4. Очистить только цели (savings_goals)
5. Очистить только напоминания (reminders)
6. Очистить только пользователей (users)
7. Очистить данные конкретного пользователя
8. Показать статистику
0. Выход
"""
    print(menu)

    while True:
        try:
            choice = input("\nВведите номер действия: ").strip()

            if choice == "0":
                print("👋 До свидания!")
                break
            elif choice == "1":
                confirm = input("⚠️ Удалить ВСЕ данные? введите 'yes': ").strip().lower()
                if confirm == 'yes':
                    clear_all_tables()
            elif choice == "2":
                clear_specific_table('expenses')
            elif choice == "3":
                clear_specific_table('budgets')
            elif choice == "4":
                clear_specific_table('savings_goals')
            elif choice == "5":
                clear_specific_table('reminders')
            elif choice == "6":
                clear_specific_table('users')
            elif choice == "7":
                user_id = input("Введите user_id пользователя: ").strip()
                try:
                    clear_user_data(int(user_id))
                except ValueError:
                    print("❌ Некорректный user_id")
            elif choice == "8":
                show_database_stats()
            else:
                print("❌ Неверный выбор!")
        except KeyboardInterrupt:
            print("\n\n👋 До свидания!")
            break
        except Exception as error:
            print(f"❌ Ошибка: {error}")


if __name__ == "__main__":
    main()
