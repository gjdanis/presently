"""Database connection and utilities."""

import os
from contextlib import contextmanager
from typing import Any, Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from .logger import setup_logger

# Global connection pool
_connection_pool: pool.SimpleConnectionPool | None = None

logger = setup_logger(__name__)


def get_connection_pool() -> pool.SimpleConnectionPool:
    """Get or create the database connection pool."""
    global _connection_pool

    if _connection_pool is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")

        _connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=database_url,
        )

    return _connection_pool


@contextmanager
def get_db_connection() -> Generator[Any, None, None]:
    """
    Get a database connection from the pool.

    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM profiles")
                results = cur.fetchall()
    """
    pool_instance = get_connection_pool()
    conn = pool_instance.getconn()

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool_instance.putconn(conn)


@contextmanager
def get_db_cursor(dict_cursor: bool = True) -> Generator[Any, None, None]:
    """
    Get a database cursor with automatic connection handling.

    Args:
        dict_cursor: If True, use RealDictCursor for dict-like results

    Usage:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM profiles WHERE id = %s", (user_id,))
            result = cur.fetchone()
    """
    with get_db_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()


def execute_query(
    query: str, params: tuple[Any, ...] | None = None, fetch_one: bool = False
) -> Any:
    """
    Execute a query and return results.

    Args:
        query: SQL query string
        params: Query parameters
        fetch_one: If True, return single row; otherwise return all rows

    Returns:
        Single dict (if fetch_one=True) or list of dicts
    """
    logger.debug(f"Executing query: {query.strip()[:100]}...")

    try:
        with get_db_cursor() as cur:
            cur.execute(query, params or ())
            if fetch_one:
                result = cur.fetchone()
                logger.debug(f"Query returned: {1 if result else 0} row")
                return result
            results = cur.fetchall()
            logger.debug(f"Query returned: {len(results)} rows")
            return results
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}", exc_info=True)
        raise


def execute_insert(query: str, params: tuple[Any, ...]) -> Any:
    """
    Execute an INSERT query and return the inserted row.

    Args:
        query: SQL INSERT query with RETURNING clause
        params: Query parameters

    Returns:
        Dict of inserted row
    """
    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def execute_update(query: str, params: tuple[Any, ...]) -> int:
    """
    Execute an UPDATE query and return number of affected rows.

    Args:
        query: SQL UPDATE query
        params: Query parameters

    Returns:
        Number of affected rows
    """
    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.rowcount


def execute_delete(query: str, params: tuple[Any, ...]) -> int:
    """
    Execute a DELETE query and return number of affected rows.

    Args:
        query: SQL DELETE query
        params: Query parameters

    Returns:
        Number of affected rows
    """
    with get_db_cursor() as cur:
        cur.execute(query, params)
        return cur.rowcount
