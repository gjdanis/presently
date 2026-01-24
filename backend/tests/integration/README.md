## Integration Tests

Integration tests run against a **real PostgreSQL database** using Docker.

### Quick Start

```bash
# Run all integration tests (automatically starts/stops Docker)
make test-integration

# Run with coverage
make test-integration-cov
```

### Manual Docker Control

```bash
# Start test database
make docker-test-up

# Run tests manually
export TEST_DATABASE_URL='postgresql://test:test@localhost:5433/presently_test'
pytest backend/tests/integration -v

# Stop test database
make docker-test-down
```

### What Integration Tests Cover

- **Real database queries**: Tests actual SQL execution
- **Database constraints**: Tests foreign keys, unique constraints, etc.
- **Transaction handling**: Tests rollback, commit behavior
- **Data integrity**: Tests CASCADE deletes, triggers, etc.
- **Full request flow**: Tests handler → database → response

### Test Isolation

Each test runs in its own transaction and database state:

1. **`clean_db` fixture**: Truncates all tables before each test
2. **Sample data fixtures**: Create common test data (profiles, groups)
3. **No test pollution**: Each test starts with a clean slate

### Writing Integration Tests

```python
def test_my_feature(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test description."""
    # Use sample_profile for pre-created user
    # Or create your own test data

    from handlers.my_handler import my_function

    response = my_function(sample_profile["id"])

    assert response["statusCode"] == 200

    # Verify in database
    from common.db import execute_query

    result = execute_query(
        "SELECT * FROM my_table WHERE id = %s",
        (some_id,),
        fetch_one=True
    )

    assert result is not None
```

### Available Fixtures

- **`clean_db`**: Clean database connection (all tables truncated)
- **`sample_profile`**: Pre-created user profile
- **`sample_group`**: Pre-created group with sample_profile as admin

### Debugging Tests

```bash
# Run specific test
pytest backend/tests/integration/test_profile_integration.py::test_get_profile_success -v

# Run with database logs
export LOG_LEVEL=DEBUG
pytest backend/tests/integration -v

# Keep database running for inspection
make docker-test-up
psql postgresql://test:test@localhost:5433/presently_test
# (database stays running until you run: make docker-test-down)
```

### CI/CD

Integration tests are designed to run in CI:

```yaml
# Example GitHub Actions
- name: Start test database
  run: docker-compose -f docker-compose.test.yml up -d

- name: Run integration tests
  run: |
    export TEST_DATABASE_URL='postgresql://test:test@localhost:5433/presently_test'
    make test-integration

- name: Cleanup
  run: docker-compose -f docker-compose.test.yml down -v
```
