"""FastAPI database dependency."""

from typing import Generator
from common.db import get_db_connection, return_db_connection


def get_db() -> Generator:
    """
    FastAPI dependency for database connections.

    Yields a database connection and ensures it's returned to the pool.
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        return_db_connection(conn)
