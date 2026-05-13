.PHONY: venv up down dev build install install-uv migrate create-key revoke-key test test-verbose lint typecheck clean format help

APP_NAME = langgraph-fastapi-starter
PYTHON = python3

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

venv: ## Create a local virtual environment in .venv
	@echo "→ Creating virtual environment..."
	$(PYTHON) -m venv .venv

up: ## Start postgres via Docker Compose
	@echo "→ Starting database..."
	docker compose up -d
	@echo "→ Waiting for postgres to be ready..."
	@sleep 2
	@docker compose exec postgres pg_isready -U agent -d agentdb || sleep 3

down: ## Stop and remove containers
	@echo "→ Stopping containers..."
	docker compose down

install: ## Install package in editable mode with dev dependencies
	@echo "→ Installing dependencies..."
	$(PYTHON) -m pip install -e ".[dev]"

install-uv: ## Install dev dependencies with uv into the selected Python environment
	@echo "→ Installing dependencies with uv..."
	uv pip install --python $(PYTHON) -e ".[dev]"

migrate: ## Run database migrations
	@echo "→ Running migrations..."
	alembic upgrade head

create-key: ## Create an API key. Usage: make create-key NAME="my-key" ROLE="admin"
	@echo "→ Creating API key..."
	$(PYTHON) scripts/create_api_key.py --name "$(NAME)" --role "$(or $(ROLE),user)"

revoke-key: ## Revoke an API key by ID. Usage: make revoke-key ID="uuid-here"
	@echo "→ Revoking key $(ID)..."
	$(PYTHON) scripts/revoke_api_key.py --id "$(ID)" --yes

dev: ## Run development server with auto-reload
	@echo "→ Starting dev server on http://localhost:8000"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level warning

test: ## Run test suite
	@echo "→ Running tests..."
	pytest -q --tb=short

test-verbose: ## Run tests with verbose output
	pytest -v --tb=long

lint: ## Run ruff linter
	ruff check app/ tests/ scripts/

typecheck: ## Run mypy type checker
	mypy app/ --ignore-missing-imports

clean: ## Remove Python cache files and test artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf .mypy_cache .pytest_cache .ruff_cache

format: ## Auto-fix linting issues
	ruff check --fix app/ tests/ scripts/
	ruff format app/ tests/ scripts/
