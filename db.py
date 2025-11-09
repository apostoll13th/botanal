import os
import time

import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/expenses"


def get_database_url() -> str:
    """
    Returns the database URL from env or the local default.
    """
    return os.getenv("DATABASE_URL", DEFAULT_DB_URL)


def get_db_connection():
    """
    Create a new database connection with RealDictCursor by default.
    The caller is responsible for closing the connection.
    """
    return psycopg2.connect(
        get_database_url(),
        cursor_factory=RealDictCursor,
    )


def wait_for_db(max_attempts: int = 10, delay_seconds: int = 2):
    """
    Blocks until the database becomes available or raises the last exception.
    """
    last_exc = None
    for _ in range(max_attempts):
        try:
            conn = get_db_connection()
            conn.close()
            return
        except psycopg2.OperationalError as exc:
            last_exc = exc
            time.sleep(delay_seconds)
    if last_exc:
        raise last_exc
