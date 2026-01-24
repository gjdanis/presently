# Testing Guide

Complete testing setup for the Presently backend.

## Test Types

### 1. Unit Tests (33 tests)
Fast tests with mocked dependencies.

```bash
make test              # Run all unit tests
make test-cov          # Run with coverage report
make test-quick        # Run without coverage (faster)
```

**What's tested:**
- ✅ Response formatting (JSON, error codes)
- ✅ Request validation (Pydantic models)
- ✅ Authentication (JWT verification)
- ✅ Handler routing

**Speed:** ~0.5 seconds

---

### 2. Integration Tests (23 tests)
Real database tests using Docker PostgreSQL.

```bash
make test-integration      # Auto starts/stops Docker
make test-integration-cov  # With coverage report
```

**What's tested:**
- ✅ Real SQL queries
- ✅ Database constraints (foreign keys, CASCADE)
- ✅ Authorization rules (admin-only, owner-only)
- ✅ Transaction handling
- ✅ Full handler → database → response flow

**Speed:** ~10 seconds (includes Docker startup)

**Requires:** Docker installed and running

---

## Quick Start

```bash
# Install dependencies
make install-dev

# Run unit tests
make test

# Run integration tests (requires Docker)
make test-integration
```

---

## Manual Integration Testing

```bash
# Start test database
make docker-test-up

# Connect to database
psql postgresql://test:test@localhost:5433/presently_test

# Run specific test
export TEST_DATABASE_URL='postgresql://test:test@localhost:5433/presently_test'
pytest backend/tests/integration/test_profile_integration.py::test_get_profile_success -v

# View logs with DEBUG level
export LOG_LEVEL=DEBUG
pytest backend/tests/integration -v

# Stop database when done
make docker-test-down
```

---

## Test Structure

```
backend/tests/
├── conftest.py                      # Unit test fixtures
├── test_auth.py                     # Auth utils tests
├── test_profile.py                  # Profile handler tests
├── test_responses.py                # Response helpers tests
├── test_validators.py               # Validation tests
└── integration/
    ├── conftest.py                  # Integration test fixtures
    ├── test_profile_integration.py  # Profile with real DB
    ├── test_groups_integration.py   # Groups with real DB
    └── test_wishlist_integration.py # Wishlist with real DB
```

---

## Writing Tests

### Unit Test Example

```python
from unittest.mock import patch
from handlers.profile import get_profile

@patch("handlers.profile.execute_query")
def test_get_profile(mock_query):
    mock_query.return_value = {
        "id": "123",
        "email": "test@example.com",
        "name": "Test User"
    }

    response = get_profile("123")

    assert response["statusCode"] == 200
```

### Integration Test Example

```python
def test_create_group(clean_db, sample_profile):
    """Test with real database."""
    from handlers.groups import create_group

    event = {"body": json.dumps({"name": "Test Group"})}
    response = create_group(event, sample_profile["id"])

    assert response["statusCode"] == 201

    # Verify in database
    from common.db import execute_query
    group = execute_query(
        "SELECT * FROM groups WHERE name = %s",
        ("Test Group",),
        fetch_one=True
    )
    assert group is not None
```

---

## Available Fixtures

### Unit Tests
- `mock_db_connection` - Mocked database connection
- `mock_auth` - Mocked authentication
- `mock_event` - Lambda event dict
- `mock_context` - Lambda context

### Integration Tests
- `clean_db` - Real database with all tables truncated
- `sample_profile` - Pre-created test user
- `sample_group` - Pre-created test group (with sample_profile as admin)

---

## Coverage

View coverage report after running:

```bash
make test-cov              # Unit test coverage
make test-integration-cov  # Integration test coverage

# Open HTML report
open backend/htmlcov/index.html
```

---

## CI/CD Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: presently_test
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: make install-dev

      - name: Run unit tests
        run: make test-cov

      - name: Run integration tests
        env:
          TEST_DATABASE_URL: postgresql://test:test@localhost:5433/presently_test
        run: |
          psql $TEST_DATABASE_URL -f backend/migrations/schema.sql
          make test-integration-cov
```

---

## Debugging Tests

### Run specific test file
```bash
pytest backend/tests/test_profile.py -v
```

### Run specific test
```bash
pytest backend/tests/test_profile.py::test_get_profile_success -v
```

### Show print statements
```bash
pytest backend/tests -v -s
```

### Stop on first failure
```bash
pytest backend/tests -x
```

### Run last failed tests
```bash
pytest backend/tests --lf
```

---

## Common Issues

### "Database connection refused"
- Make sure Docker is running
- Run `make docker-test-up` before manual integration tests
- Check port 5433 is not in use: `lsof -i :5433`

### "Module not found"
- Run `make install-dev` to install dependencies
- Make sure virtual environment is activated

### "Fixture not found"
- Check you're using the right conftest.py
- Unit tests: `backend/tests/conftest.py`
- Integration tests: `backend/tests/integration/conftest.py`

---

## Performance

| Test Type | Count | Duration | Database |
|-----------|-------|----------|----------|
| Unit | 33 | ~0.5s | Mocked |
| Integration | 23 | ~10s | Real (Docker) |
| **Total** | **56** | **~10.5s** | Mixed |

All tests should complete in under 15 seconds on most machines.
