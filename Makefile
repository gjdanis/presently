.PHONY: help install test lint format frontend backend db-local-up db-local-down seed deploy-dev clean

# Variables
BACKEND_DIR := backend
LAMBDA_DIR := $(BACKEND_DIR)/lambda
FRONTEND_DIR := frontend
VENV_DIR := $(BACKEND_DIR)/venv
PYTHON := $(shell pwd)/$(VENV_DIR)/bin/python3
PIP := $(shell pwd)/$(VENV_DIR)/bin/pip

# Check if virtual environment exists
VENV_EXISTS := $(shell [ -d "$(VENV_DIR)" ] && echo 1 || echo 0)

# Default target
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                Presently - Development Makefile                ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make install        - Install all dependencies"
	@echo "  make db-local-up    - Start local Postgres database"
	@echo "  make seed           - Seed database with test data"
	@echo "  make backend        - Start backend API (localhost:8000)"
	@echo "  make frontend       - Start frontend (localhost:3000)"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test           - Run all tests (unit + integration)"
	@echo "  make lint           - Lint backend AND frontend code"
	@echo "  make format         - Format all code"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  make db-local-up    - Start local Postgres"
	@echo "  make db-local-down  - Stop local Postgres"
	@echo "  make seed           - Seed local database with test data"
	@echo "  make db-migrate     - Run migrations on dev database"
	@echo ""
	@echo "🚢 Deployment:"
	@echo "  make deploy-dev     - Deploy to dev environment (AWS)"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make clean-all      - Remove everything including venv"
	@echo ""
	@if [ "$(VENV_EXISTS)" = "0" ]; then \
		echo "⚠️  Run 'make install' to set up your environment"; \
	else \
		echo "✅ Environment ready!"; \
	fi

# ============================================================================
# Installation
# ============================================================================

install:
	@echo "📦 Installing all dependencies..."
	@$(MAKE) _venv
	@$(MAKE) _install-backend
	@$(MAKE) _install-frontend
	@echo ""
	@echo "✅ All dependencies installed!"
	@echo ""
	@echo "🚀 Next steps:"
	@echo "  1. Run: make db-local-up"
	@echo "  2. Run: make seed"
	@echo "  3. Run: make backend (in one terminal)"
	@echo "  4. Run: make frontend (in another terminal)"

_venv:
	@if [ "$(VENV_EXISTS)" = "0" ]; then \
		echo "📦 Creating Python virtual environment..."; \
		if command -v python3.11 >/dev/null 2>&1; then \
			PYTHON_CMD=python3.11; \
		elif command -v python3.12 >/dev/null 2>&1; then \
			PYTHON_CMD=python3.12; \
		elif python3 --version 2>&1 | grep -qE 'Python 3\.(1[1-9]|[2-9][0-9])'; then \
			PYTHON_CMD=python3; \
		else \
			echo "❌ Python 3.11+ required"; \
			exit 1; \
		fi; \
		$$PYTHON_CMD -m venv $(VENV_DIR); \
		$(PIP) install --upgrade pip setuptools wheel; \
		echo "✅ Virtual environment created"; \
	fi

_install-backend:
	@echo "📦 Installing backend dependencies..."
	@$(PIP) install -r $(BACKEND_DIR)/requirements.txt
	@echo "✅ Backend dependencies installed"

_install-frontend:
	@echo "📦 Installing frontend dependencies..."
	@if ! command -v node >/dev/null 2>&1; then \
		echo "❌ Node.js not installed. Install from https://nodejs.org/"; \
		exit 1; \
	fi
	@cd $(FRONTEND_DIR) && npm install
	@echo "✅ Frontend dependencies installed"

# ============================================================================
# Testing
# ============================================================================

test:
	@echo "🧪 Running all tests (unit + integration)..."
	@echo ""
	@echo "▶ Running unit tests..."
	@$(PYTHON) -m pytest $(BACKEND_DIR)/tests --ignore=$(BACKEND_DIR)/tests/integration -v
	@echo ""
	@echo "▶ Running integration tests..."
	@$(MAKE) _test-integration
	@echo ""
	@echo "✅ All tests passed!"

_test-integration:
	@echo "🐳 Starting test database..."
	@docker-compose -f docker-compose.test.yml up -d
	@sleep 5
	@export TEST_DATABASE_URL='postgresql://test:test@localhost:5433/presently_test' && \
		$(PYTHON) -m pytest $(BACKEND_DIR)/tests/integration -v || \
		(docker-compose -f docker-compose.test.yml down -v && exit 1)
	@docker-compose -f docker-compose.test.yml down -v
	@echo "✅ Integration tests complete"

# ============================================================================
# Linting & Formatting
# ============================================================================

lint:
	@echo "🔍 Linting all code..."
	@echo ""
	@echo "▶ Backend (Python):"
	@$(PYTHON) -m ruff check $(LAMBDA_DIR)
	@echo ""
	@echo "▶ Frontend (TypeScript):"
	@cd $(FRONTEND_DIR) && ESLINT_USE_FLAT_CONFIG=false npm run lint
	@echo ""
	@echo "✅ Linting complete!"

format:
	@echo "✨ Formatting all code..."
	@echo ""
	@echo "▶ Backend (Python):"
	@$(PYTHON) -m ruff format $(LAMBDA_DIR)
	@$(PYTHON) -m ruff check --fix $(LAMBDA_DIR)
	@echo ""
	@echo "▶ Frontend (TypeScript):"
	@cd $(FRONTEND_DIR) && npm run lint --fix 2>/dev/null || echo "Note: Next.js lint auto-fix may not be available"
	@echo ""
	@echo "✅ Formatting complete!"

# ============================================================================
# Local Development
# ============================================================================

frontend:
	@echo "🚀 Starting frontend development server..."
	@if [ ! -d "$(FRONTEND_DIR)/node_modules" ]; then \
		echo "❌ Frontend dependencies not installed. Run 'make install' first"; \
		exit 1; \
	fi
	@if [ ! -f ".env.local" ]; then \
		echo "❌ .env.local not found"; \
		echo "   Copy .env.local.example to .env.local and configure"; \
		exit 1; \
	fi
	@echo ""
	@echo "Frontend will be available at: http://localhost:3000"
	@echo "Loading environment from .env.local"
	@echo ""
	@cd $(FRONTEND_DIR) && set -a && . ../.env.local && set +a && npm run dev

backend:
	@echo "🚀 Starting backend development server..."
	@if [ "$(VENV_EXISTS)" = "0" ]; then \
		echo "❌ Backend dependencies not installed. Run 'make install' first"; \
		exit 1; \
	fi
	@if [ ! -f ".env.local" ]; then \
		echo "❌ .env.local not found"; \
		echo "   Copy .env.local.example to .env.local and configure"; \
		exit 1; \
	fi
	@echo ""
	@echo "Backend API will be available at: http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/docs"
	@echo "Loading environment from .env.local"
	@echo ""
	@export $$(cat .env.local | grep -v '^#' | grep -v '^$$' | xargs) && \
		cd $(LAMBDA_DIR) && $(PYTHON) main.py

# ============================================================================
# Database Management
# ============================================================================

db-local-up:
	@echo "🐳 Starting local Postgres database..."
	@docker-compose -f docker-compose.local.yml up -d
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@echo "✅ Local database is ready!"
	@echo ""
	@echo "📋 Connection details:"
	@echo "   Host: localhost"
	@echo "   Port: 5433"
	@echo "   Database: presently_local"
	@echo "   User: presently"
	@echo "   Password: presently_local"
	@echo ""
	@echo "Connection string:"
	@echo "   postgresql://presently:presently_local@localhost:5433/presently_local"
	@echo ""
	@echo "💡 Next: Run 'make seed' to add test data"

db-local-down:
	@echo "🛑 Stopping local database..."
	@docker-compose -f docker-compose.local.yml down
	@echo "✅ Local database stopped"
	@echo ""
	@echo "💡 Data is persisted. Run 'docker-compose -f docker-compose.local.yml down -v' to delete data"

seed:
	@echo "🌱 Seeding local database with test data..."
	@DATABASE_URL=postgresql://presently:presently_local@localhost:5433/presently_local \
		$(PYTHON) $(BACKEND_DIR)/scripts/seed_local.py

db-migrate:
	@echo "🗃️  Running database migrations on dev environment..."
	@if [ ! -f ".env.local" ]; then \
		echo "❌ .env.local not found"; \
		echo "   Copy .env.local.example to .env.local and configure"; \
		exit 1; \
	fi
	@export $$(cat .env.local | grep -v '^#' | grep -v '^$$' | xargs) && \
		psql "$$DATABASE_URL" -f $(BACKEND_DIR)/migrations/schema.sql
	@echo "✅ Migrations complete!"

# ============================================================================
# Deployment
# ============================================================================

deploy-dev:
	@echo "🚀 Deploying to dev environment..."
	@if [ ! -f ".env.local" ]; then \
		echo "❌ .env.local not found"; \
		echo "   Copy .env.local.example to .env.local and configure"; \
		exit 1; \
	fi
	@echo ""
	@echo "📄 Loading environment variables from .env.local..."
	@export $$(cat .env.local | grep -v '^#' | grep -v '^$$' | xargs) && \
	if [ -z "$$DATABASE_URL" ]; then \
		echo "❌ DATABASE_URL not set in .env.local"; \
		exit 1; \
	fi && \
	if [ -z "$$SENDER_EMAIL" ]; then \
		echo "❌ SENDER_EMAIL not set in .env.local"; \
		exit 1; \
	fi && \
	FRONTEND_URL=$${FRONTEND_URL:-https://presently-nu.vercel.app} && \
	echo "✅ Environment variables loaded" && \
	echo "" && \
	echo "📦 Building SAM application..." && \
	cd infrastructure && sam build && \
	echo "" && \
	echo "🚀 Deploying to AWS..." && \
	sam deploy \
		--template-file .aws-sam/build/template.yaml \
		--stack-name presently-dev \
		--region us-east-1 \
		--parameter-overrides \
			Environment=dev \
			NeonDatabaseURL="$$DATABASE_URL" \
			SenderEmail="$$SENDER_EMAIL" \
			FrontendURL="$$FRONTEND_URL" \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
		--resolve-s3 \
		--no-fail-on-empty-changeset && \
	echo "" && \
	echo "✅ Deployment complete!" && \
	echo "" && \
	echo "📋 API Gateway URL:" && \
	aws cloudformation describe-stacks \
		--stack-name presently-dev \
		--region us-east-1 \
		--query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
		--output text && \
	echo "" && \
	echo "💡 Next steps:" && \
	echo "  1. Update NEXT_PUBLIC_API_URL in .env.local with the URL above" && \
	echo "  2. Deploy frontend to Vercel"

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "🧹 Cleaning build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf $(BACKEND_DIR)/.aws-sam 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/.next 2>/dev/null || true
	@echo "✅ Build artifacts cleaned"

clean-all: clean
	@echo "🧹 Removing virtual environment..."
	@rm -rf $(VENV_DIR)
	@echo "🧹 Removing node_modules..."
	@rm -rf $(FRONTEND_DIR)/node_modules
	@echo "✅ Everything cleaned"
