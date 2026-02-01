"""Integration test fixtures and configuration."""

import os
import time
from typing import Any, Generator

import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Get test database URL - uses the local Docker database."""
    # Use the local Docker database (presently-local-db on port 5433)
    test_url = "postgresql://presently:presently_local@localhost:5433/presently_local"

    # Override environment to ensure we use test database
    os.environ["DATABASE_URL"] = test_url

    return test_url


@pytest.fixture(scope="session")
def wait_for_db(test_db_url: str) -> None:
    """Wait for database to be ready."""
    max_retries = 30
    retry_interval = 1

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(test_db_url)
            conn.close()
            print("✅ Database is ready!")
            return
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                print(f"⏳ Waiting for database... ({i + 1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                raise

    raise RuntimeError("Database did not become ready in time")


@pytest.fixture(scope="function")
def db_connection(test_db_url: str, wait_for_db: None) -> Generator[Any, None, None]:
    """
    Provide a database connection for a test.

    Each test gets a fresh transaction that is rolled back after the test,
    ensuring test isolation.
    """
    # Set DATABASE_URL for the common.db module
    os.environ["DATABASE_URL"] = test_db_url

    # Clear any existing connection pool
    import common.db as db_module
    if db_module._connection_pool:
        db_module._connection_pool.closeall()
        db_module._connection_pool = None

    # Create a new connection for this test
    conn = psycopg2.connect(test_db_url)

    # Start a transaction
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    yield conn

    # Rollback and close
    conn.close()


@pytest.fixture(scope="function")
def clean_db(db_connection: Any) -> Generator[Any, None, None]:
    """
    Provide a clean database for each test.

    Truncates all tables before the test runs.
    """
    cursor = db_connection.cursor()

    # Disable foreign key checks temporarily
    cursor.execute("SET session_replication_role = 'replica';")

    # Get all table names
    cursor.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT LIKE 'pg_%'
    """)

    tables = [row[0] for row in cursor.fetchall()]

    # Truncate all tables
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table} CASCADE")

    # Re-enable foreign key checks
    cursor.execute("SET session_replication_role = 'origin';")

    db_connection.commit()
    cursor.close()

    yield db_connection


@pytest.fixture
def sample_profile(clean_db: Any) -> dict[str, Any]:
    """Create a sample user profile for testing."""
    from uuid import uuid4

    user_id = uuid4()
    email = f"test-{uuid4()}@example.com"

    cursor = clean_db.cursor()
    cursor.execute(
        """
        INSERT INTO profiles (id, email, name)
        VALUES (%s, %s, %s)
        RETURNING id, email, name, created_at, updated_at
        """,
        (str(user_id), email, "Test User")
    )

    result = cursor.fetchone()
    clean_db.commit()
    cursor.close()

    return {
        "id": str(result[0]),
        "email": result[1],
        "name": result[2],
        "created_at": result[3],
        "updated_at": result[4],
    }


@pytest.fixture
def sample_group(clean_db: Any, sample_profile: dict[str, Any]) -> dict[str, Any]:
    """Create a sample group for testing."""
    cursor = clean_db.cursor()

    # Create group
    cursor.execute(
        """
        INSERT INTO groups (name, description, created_by)
        VALUES (%s, %s, %s)
        RETURNING id, name, description, created_by, created_at, updated_at
        """,
        ("Test Group", "A test group", sample_profile["id"])
    )

    group_result = cursor.fetchone()

    # Add creator as admin
    cursor.execute(
        """
        INSERT INTO group_memberships (user_id, group_id, role)
        VALUES (%s, %s, %s)
        """,
        (sample_profile["id"], str(group_result[0]), "admin")
    )

    clean_db.commit()
    cursor.close()

    return {
        "id": str(group_result[0]),
        "name": group_result[1],
        "description": group_result[2],
        "created_by": str(group_result[3]),
        "created_at": group_result[4],
        "updated_at": group_result[5],
    }
