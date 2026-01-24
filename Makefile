.PHONY: help install install-dev test test-quick test-cov test-integration test-integration-cov lint format check clean deploy-infra deploy-lambda configure-cognito-triggers deploy db-migrate db-shell venv docker-test-up docker-test-down

# Variables
BACKEND_DIR := backend
LAMBDA_DIR := $(BACKEND_DIR)/lambda
INFRA_DIR := infrastructure
VENV_DIR := $(BACKEND_DIR)/venv
PYTHON := $(VENV_DIR)/bin/python3
PIP := $(VENV_DIR)/bin/pip

# Check if virtual environment exists
VENV_EXISTS := $(shell [ -d "$(VENV_DIR)" ] && echo 1 || echo 0)

# Default target
help:
	@echo "Presently - AWS Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  venv            - Create Python virtual environment"
	@echo "  install         - Install production dependencies (creates venv if needed)"
	@echo "  install-dev     - Install production + development dependencies"
	@echo "  test            - Run unit tests"
	@echo "  test-cov        - Run unit tests with coverage report"
	@echo "  test-quick      - Run unit tests (fast, no coverage)"
	@echo "  test-integration - Run integration tests (requires Docker)"
	@echo "  test-integration-cov - Run integration tests with coverage"
	@echo "  docker-test-up  - Start test database in Docker"
	@echo "  docker-test-down - Stop test database"
	@echo "  lint            - Run ruff linter"
	@echo "  format          - Format code with ruff"
	@echo "  check           - Run type checking with mypy"
	@echo "  clean           - Remove build artifacts and cache files"
	@echo "  clean-all       - Remove build artifacts and virtual environment"
	@echo "  deploy-infra    - Deploy infrastructure (Cognito, S3)"
	@echo "  deploy-lambda   - Deploy Lambda functions"
	@echo "  configure-cognito-triggers - Configure Cognito Lambda triggers"
	@echo "  deploy          - Deploy infrastructure, Lambda, and configure triggers"
	@echo "  db-migrate      - Run database migrations"
	@echo "  db-shell        - Open PostgreSQL shell"
	@echo ""
	@if [ "$(VENV_EXISTS)" = "0" ]; then \
		echo "⚠️  Virtual environment not found. Run 'make venv' or 'make install-dev' to create it."; \
	else \
		echo "✅ Virtual environment active at: $(VENV_DIR)"; \
	fi

# Create virtual environment
venv:
	@if [ "$(VENV_EXISTS)" = "1" ]; then \
		echo "✅ Virtual environment already exists at: $(VENV_DIR)"; \
	else \
		echo "📦 Creating virtual environment..."; \
		echo "Detecting Python 3.11+..."; \
		if command -v python3.11 >/dev/null 2>&1; then \
			PYTHON_CMD=python3.11; \
		elif command -v python3.12 >/dev/null 2>&1; then \
			PYTHON_CMD=python3.12; \
		elif command -v python3.13 >/dev/null 2>&1; then \
			PYTHON_CMD=python3.13; \
		elif python3 --version 2>&1 | grep -qE 'Python 3\.(1[1-9]|[2-9][0-9])'; then \
			PYTHON_CMD=python3; \
		else \
			echo "❌ Error: Python 3.11+ is required"; \
			echo "Found: $$(python3 --version 2>&1)"; \
			echo ""; \
			echo "Install Python 3.11+ using one of:"; \
			echo "  - Homebrew: brew install python@3.11"; \
			echo "  - pyenv: pyenv install 3.11 && pyenv local 3.11"; \
			echo "  - Official installer: https://www.python.org/downloads/"; \
			exit 1; \
		fi; \
		echo "Using: $$PYTHON_CMD ($$($$PYTHON_CMD --version))"; \
		$$PYTHON_CMD -m venv $(VENV_DIR); \
		$(PIP) install --upgrade pip setuptools wheel; \
		echo "✅ Virtual environment created at: $(VENV_DIR)"; \
		echo ""; \
		echo "To activate manually:"; \
		echo "  source $(VENV_DIR)/bin/activate"; \
	fi

# Install production dependencies
install: venv
	@echo "📦 Installing production dependencies..."
	$(PIP) install -r $(BACKEND_DIR)/requirements-layer.txt
	@echo "✅ Production dependencies installed"

# Install development dependencies
install-dev: venv
	@echo "📦 Installing development dependencies..."
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt
	@echo "✅ Development dependencies installed"
	@echo ""
	@echo "Virtual environment ready! Makefile will use it automatically."
	@echo "To activate manually: source $(VENV_DIR)/bin/activate"

# Run tests with coverage
test:
	@if ! $(PYTHON) -m pytest --version >/dev/null 2>&1; then \
		echo "❌ Error: pytest not installed. Run 'make install-dev' first"; \
		exit 1; \
	fi
	$(PYTHON) -m pytest $(BACKEND_DIR)/tests --ignore=$(BACKEND_DIR)/tests/integration

# Run tests without coverage (faster)
test-quick:
	$(PYTHON) -m pytest -v $(BACKEND_DIR)/tests --ignore=$(BACKEND_DIR)/tests/integration

# Run tests with coverage report
test-cov:
	@if ! $(PYTHON) -c "import pytest_cov" 2>/dev/null; then \
		echo "❌ Error: pytest-cov not installed. Run 'make install-dev' first"; \
		exit 1; \
	fi
	$(PYTHON) -m pytest -v --cov=lambda --cov-report=html --cov-report=term-missing $(BACKEND_DIR)/tests --ignore=$(BACKEND_DIR)/tests/integration
	@echo ""
	@echo "📊 Coverage report generated: backend/htmlcov/index.html"

# Start test database
docker-test-up:
	@echo "🐳 Starting test database..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@echo "✅ Test database is ready!"
	@echo ""
	@echo "Connection string: postgresql://test:test@localhost:5433/presently_test"

# Stop test database
docker-test-down:
	@echo "🛑 Stopping test database..."
	docker-compose -f docker-compose.test.yml down -v
	@echo "✅ Test database stopped and data cleaned"

# Run integration tests
test-integration: docker-test-up
	@echo "🧪 Running integration tests..."
	@export TEST_DATABASE_URL='postgresql://test:test@localhost:5433/presently_test' && \
		$(PYTHON) -m pytest -v $(BACKEND_DIR)/tests/integration
	@$(MAKE) docker-test-down

# Run integration tests with coverage
test-integration-cov: docker-test-up
	@echo "🧪 Running integration tests with coverage..."
	@export TEST_DATABASE_URL='postgresql://test:test@localhost:5433/presently_test' && \
		$(PYTHON) -m pytest -v --cov=lambda --cov-report=html --cov-report=term-missing $(BACKEND_DIR)/tests/integration
	@echo ""
	@echo "📊 Coverage report generated: backend/htmlcov/index.html"
	@$(MAKE) docker-test-down

# Run linter
lint:
	$(PYTHON) -m ruff check $(LAMBDA_DIR)

# Format code
format:
	$(PYTHON) -m ruff format $(LAMBDA_DIR)
	$(PYTHON) -m ruff check --fix $(LAMBDA_DIR)

# Type checking
check:
	$(PYTHON) -m mypy $(LAMBDA_DIR)

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(BACKEND_DIR)/.aws-sam 2>/dev/null || true
	@echo "✅ Build artifacts cleaned"

# Clean everything including virtual environment
clean-all: clean
	@echo "🧹 Removing virtual environment..."
	rm -rf $(VENV_DIR)
	@echo "✅ Everything cleaned"

# Deploy infrastructure (Cognito + S3)
deploy-infra:
	@echo "Deploying infrastructure..."
	@if [ -z "$(ENV)" ]; then \
		echo "Error: ENV variable is required. Usage: make deploy-infra ENV=prod"; \
		exit 1; \
	fi
	cd $(INFRA_DIR) && ./scripts/deploy-infra.sh $(ENV)

# Deploy Lambda functions
deploy-lambda:
	@echo "Deploying Lambda functions..."
	@if [ -z "$(ENV)" ]; then \
		echo "Error: ENV variable is required. Usage: make deploy-lambda ENV=prod"; \
		exit 1; \
	fi
	cd $(INFRA_DIR) && ./scripts/deploy-lambda.sh $(ENV)

# Configure Cognito Lambda triggers
configure-cognito-triggers:
	@echo "Configuring Cognito Lambda triggers..."
	@if [ -z "$(ENV)" ]; then \
		echo "Error: ENV variable is required. Usage: make configure-cognito-triggers ENV=prod"; \
		exit 1; \
	fi
	cd $(INFRA_DIR) && ./scripts/configure-cognito-triggers.sh $(ENV)

# Deploy everything
deploy:
	@if [ -z "$(ENV)" ]; then \
		echo "Error: ENV variable is required. Usage: make deploy ENV=prod"; \
		exit 1; \
	fi
	@if [ -z "$(DATABASE_URL)" ]; then \
		echo "Error: DATABASE_URL environment variable is required"; \
		echo "Set it with your Neon Postgres connection string:"; \
		echo "  export DATABASE_URL='postgresql://user:pass@host/db'"; \
		exit 1; \
	fi
	@echo "🚀 Starting full deployment for environment: $(ENV)"
	@echo ""
	$(MAKE) deploy-infra ENV=$(ENV)
	@echo ""
	$(MAKE) deploy-lambda ENV=$(ENV)
	@echo ""
	$(MAKE) configure-cognito-triggers ENV=$(ENV)
	@echo ""
	@echo "✅ Deployment complete!"
	@echo ""
	@echo "📋 Your API is ready at:"
	@aws cloudformation describe-stacks \
		--stack-name presently-lambda-$(ENV) \
		--query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
		--output text

# Run database migrations
db-migrate:
	@echo "Running database migrations..."
	@if [ -z "$(DATABASE_URL)" ]; then \
		echo "Error: DATABASE_URL environment variable is required"; \
		exit 1; \
	fi
	psql "$(DATABASE_URL)" -f $(BACKEND_DIR)/migrations/schema.sql

# Open database shell
db-shell:
	@if [ -z "$(DATABASE_URL)" ]; then \
		echo "Error: DATABASE_URL environment variable is required"; \
		exit 1; \
	fi
	psql "$(DATABASE_URL)"

# Pre-commit checks (run before committing)
pre-commit: format lint test
	@echo "✅ All pre-commit checks passed!"
