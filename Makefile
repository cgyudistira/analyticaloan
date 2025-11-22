.PHONY: help dev test lint format clean docker-build docker-up docker-down migrate seed

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# HELP
# =============================================================================
help: ## Show this help message
	@echo "$(CYAN)AnalyticaLoan - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# DEVELOPMENT
# =============================================================================
dev: ## Start all services in development mode
	@echo "$(CYAN)Starting development environment...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Infrastructure services started$(NC)"
	@echo "$(YELLOW)To start a specific service:$(NC) make dev-service NAME=auth-service"

dev-service: ## Start specific service (usage: make dev-service NAME=auth-service)
	@echo "$(CYAN)Starting $(NAME)...$(NC)"
	cd services/$(NAME) && poetry run uvicorn app.main:app --reload --port $$(grep PORT .env | cut -d '=' -f2)

stop: ## Stop all services
	@echo "$(CYAN)Stopping all services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ All services stopped$(NC)"

# =============================================================================
# INSTALLATION
# =============================================================================
install: ## Install all dependencies
	@echo "$(CYAN)Installing dependencies...$(NC)"
	poetry install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-pre-commit: ## Install pre-commit hooks
	@echo "$(CYAN)Installing pre-commit hooks...$(NC)"
	poetry run pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

# =============================================================================
# DATABASE
# =============================================================================
migrate: ## Run database migrations
	@echo "$(CYAN)Running database migrations...$(NC)"
	cd libs/database && poetry run alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed$(NC)"

migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	@echo "$(CYAN)Creating new migration: $(MSG)$(NC)"
	cd libs/database && poetry run alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	cd libs/database && poetry run alembic downgrade -1

migrate-history: ## Show migration history
	cd libs/database && poetry run alembic history

seed: ## Seed database with initial data
	@echo "$(CYAN)Seeding database...$(NC)"
	poetry run python scripts/seed_data.py
	@echo "$(GREEN)✓ Database seeded$(NC)"

db-shell: ## Open PostgreSQL shell
	docker exec -it analyticaloan-db psql -U postgres -d analyticaloan

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)⚠️  WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	$(MAKE) migrate
	$(MAKE) seed
	@echo "$(GREEN)✓ Database reset complete$(NC)"

# =============================================================================
# TESTING
# =============================================================================
test: ## Run all tests
	@echo "$(CYAN)Running all tests...$(NC)"
	poetry run pytest -v

test-unit: ## Run unit tests only
	@echo "$(CYAN)Running unit tests...$(NC)"
	poetry run pytest tests/unit -v

test-integration: ## Run integration tests
	@echo "$(CYAN)Running integration tests...$(NC)"
	docker-compose up -d
	poetry run pytest tests/integration -v

test-coverage: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	poetry run pytest --cov=services --cov=libs --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	poetry run ptw -- -v

# =============================================================================
# CODE QUALITY
# =============================================================================
lint: ## Run all linters
	@echo "$(CYAN)Running linters...$(NC)"
	poetry run black --check .
	poetry run isort --check-only .
	poetry run flake8 .
	poetry run mypy services/ libs/
	@echo "$(GREEN)✓ Linting passed$(NC)"

format: ## Auto-format code
	@echo "$(CYAN)Formatting code...$(NC)"
	poetry run black .
	poetry run isort .
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check: ## Run type checking
	@echo "$(CYAN)Running type checks...$(NC)"
	poetry run mypy services/ libs/
	@echo "$(GREEN)✓ Type checking passed$(NC)"

security-check: ## Run security vulnerability checks
	@echo "$(CYAN)Running security checks...$(NC)"
	poetry run safety check
	poetry run bandit -r services/ libs/
	@echo "$(GREEN)✓ Security check passed$(NC)"

# =============================================================================
# DOCKER
# =============================================================================
docker-build: ## Build all Docker images
	@echo "$(CYAN)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up: ## Start Docker Compose services
	@echo "$(CYAN)Starting Docker Compose...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(YELLOW)View logs:$(NC) docker-compose logs -f"

docker-down: ## Stop Docker Compose services
	@echo "$(CYAN)Stopping Docker Compose...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-logs: ## View Docker Compose logs
	docker-compose logs -f

docker-ps: ## Show running containers
	docker-compose ps

docker-clean: ## Remove all containers, volumes, and images
	@echo "$(RED)⚠️  WARNING: This will remove all Docker data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker-compose down -v --rmi all
	@echo "$(GREEN)✓ Docker cleaned$(NC)"

# =============================================================================
# UTILITIES
# =============================================================================
shell: ## Open Python shell with app context
	@echo "$(CYAN)Opening Python shell...$(NC)"
	poetry run ipython

generate-api-key: ## Generate new API key
	@echo "$(CYAN)Generating API key...$(NC)"
	poetry run python scripts/generate_api_key.py

generate-secret: ## Generate random secret key (32 bytes)
	@echo "$(CYAN)Generated Secret Key:$(NC)"
	@python -c "import secrets; print(secrets.token_urlsafe(32))"

check-deps: ## Check for outdated dependencies
	@echo "$(CYAN)Checking dependencies...$(NC)"
	poetry show --outdated

update-deps: ## Update dependencies
	@echo "$(CYAN)Updating dependencies...$(NC)"
	poetry update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

# =============================================================================
# DOCUMENTATION
# =============================================================================
docs-serve: ## Serve API documentation locally
	@echo "$(CYAN)Starting documentation server...$(NC)"
	@echo "$(GREEN)API docs available at:$(NC)"
	@echo "  - Auth Service: http://localhost:8001/docs"
	@echo "  - Application Service: http://localhost:8002/docs"
	@echo "  - Document Service: http://localhost:8003/docs"

docs-generate: ## Generate OpenAPI spec files
	@echo "$(CYAN)Generating OpenAPI specifications...$(NC)"
	poetry run python scripts/generate_openapi_specs.py
	@echo "$(GREEN)✓ OpenAPI specs generated in docs/api/$(NC)"

# =============================================================================
# MONITORING
# =============================================================================
logs: ## Tail application logs
	@echo "$(CYAN)Tailing application logs...$(NC)"
	docker-compose logs -f

metrics: ## Open Prometheus metrics UI
	@echo "$(CYAN)Opening Prometheus...$(NC)"
	@open http://localhost:9090 || xdg-open http://localhost:9090

dashboards: ## Open Grafana dashboards
	@echo "$(CYAN)Opening Grafana...$(NC)"
	@echo "$(YELLOW)Username: admin | Password: admin123$(NC)"
	@open http://localhost:3000 || xdg-open http://localhost:3000

tracing: ## Open Jaeger tracing UI
	@echo "$(CYAN)Opening Jaeger...$(NC)"
	@open http://localhost:16686 || xdg-open http://localhost:16686

temporal-ui: ## Open Temporal workflow UI
	@echo "$(CYAN)Opening Temporal UI...$(NC)"
	@open http://localhost:8081 || xdg-open http://localhost:8081

# =============================================================================
# CLEANUP
# =============================================================================
clean: ## Clean temporary files and caches
	@echo "$(CYAN)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .coverage coverage.xml
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# =============================================================================
# CI/CD
# =============================================================================
ci-test: ## Run CI test suite
	@echo "$(CYAN)Running CI test suite...$(NC)"
	$(MAKE) lint
	$(MAKE) test-coverage
	$(MAKE) security-check
	@echo "$(GREEN)✓ CI tests passed$(NC)"

build-prod: ## Build production Docker images
	@echo "$(CYAN)Building production images...$(NC)"
	docker build -f infrastructure/docker/Dockerfile.auth -t analyticaloan-auth:latest services/auth-service
	docker build -f infrastructure/docker/Dockerfile.application -t analyticaloan-application:latest services/application-service
	@echo "$(GREEN)✓ Production images built$(NC)"

# =============================================================================
# PROJECT SETUP
# =============================================================================
init: ## Initialize project (first-time setup)
	@echo "$(CYAN)Initializing AnalyticaLoan project...$(NC)"
	@echo "$(YELLOW)Step 1: Installing dependencies...$(NC)"
	$(MAKE) install
	@echo "$(YELLOW)Step 2: Copying environment file...$(NC)"
	cp .env.example .env
	@echo "$(YELLOW)Step 3: Starting infrastructure...$(NC)"
	$(MAKE) docker-up
	@echo "$(YELLOW)Step 4: Waiting for services to be ready...$(NC)"
	sleep 10
	@echo "$(YELLOW)Step 5: Running migrations...$(NC)"
	$(MAKE) migrate
	@echo "$(YELLOW)Step 6: Seeding database...$(NC)"
	$(MAKE) seed
	@echo "$(GREEN)✅ Project initialization complete!$(NC)"
	@echo ""
	@echo "$(CYAN)Next steps:$(NC)"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Run 'make dev' to start development"
	@echo "  3. Visit http://localhost:8001/docs for API documentation"

status: ## Show status of all services
	@echo "$(CYAN)Service Status:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(CYAN)Useful URLs:$(NC)"
	@echo "  • API Docs: http://localhost:8001/docs"
	@echo "  • Grafana: http://localhost:3000 (admin/admin123)"
	@echo "  • Prometheus: http://localhost:9090"
	@echo "  • Jaeger: http://localhost:16686"
	@echo "  • Temporal: http://localhost:8081"
	@echo "  • RabbitMQ: http://localhost:15672 (rabbitmq/rabbitmq123)"
	@echo "  • MinIO: http://localhost:9001 (minioadmin/minioadmin123)"

# Default target
.DEFAULT_GOAL := help
