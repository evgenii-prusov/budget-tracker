.PHONY: help install run test coverage check format lint typecheck sync clean \
        db-up db-down db-migrate db-revision db-seed \
        docker-build docker-up docker-down docker-logs dev-up dev-down \
        fe-install fe-dev fe-build fe-lint fe-preview \
        azure-provision azure-teardown deploy deploy-frontend deploy-logs deploy-status

help:
	@echo "Budget Tracker - Available Commands"
	@echo "===================================="
	@echo "make install         - Install all dependencies"
	@echo "make run             - Start backend server (local dev)"
	@echo "make test            - Run all tests  (V=1 for verbose)"
	@echo "make coverage        - Run tests with coverage  (HTML=1 for html report)"
	@echo "make check           - Run prek checks on all files"
	@echo "make format          - Format code with ruff"
	@echo "make lint            - Lint and auto-fix with ruff"
	@echo "make typecheck       - Run ty type checker"
	@echo "make sync            - Sync with remote master branch"
	@echo "make clean           - Remove generated files"
	@echo ""
	@echo "Development (local backend + Docker Postgres)"
	@echo "make dev-up          - Start Postgres only (for local dev)"
	@echo "make dev-down        - Stop Postgres only"
	@echo "make db-migrate      - Run Alembic migrations"
	@echo "make db-revision     - Create new migration (msg=\"description\")"
	@echo "make db-seed         - Seed database with sample data"
	@echo ""
	@echo "Frontend"
	@echo "make fe-install      - Install frontend dependencies"
	@echo "make fe-dev          - Start frontend dev server (port 5173)"
	@echo "make fe-build        - Production build (output: frontend/dist/)"
	@echo "make fe-lint         - Lint frontend code"
	@echo "make fe-preview      - Preview production build locally"
	@echo ""
	@echo "Production (fully Dockerised)"
	@echo "make docker-build    - Build the backend Docker image"
	@echo "make docker-up       - Start Postgres + backend via Docker Compose"
	@echo "make docker-down     - Stop and remove all Docker Compose services"
	@echo "make docker-logs     - Tail logs from all Docker Compose services"
	@echo ""
	@echo "Azure Container Apps"
	@echo "make azure-provision - One-time: create Azure infra (rg, env, app)"
	@echo "make azure-teardown  - Delete all Azure infra (irreversible, Neon untouched)"
	@echo "make deploy          - Build, push backend image to ghcr.io, update Azure app"
	@echo "make deploy-frontend - Build, push frontend image to ghcr.io, update Azure app"
	@echo "make deploy-logs     - Tail live logs from the Azure container app"
	@echo "make deploy-status   - Show running status and URL of the Azure app"

install:
	cd backend && uv sync
	cd frontend && npm ci

run:
	cd backend && uv run --env-file .env fastapi dev app/main.py

test:
	cd backend && uv run pytest$(if $(V), -v)

coverage:
	cd backend && uv run pytest --cov=app --cov-report=term-missing$(if $(HTML), --cov-report=html)
	$(if $(HTML),@echo "Coverage report generated at backend/htmlcov/index.html")

check:
	cd backend && uv run prek run --all-files

format:
	cd backend && uv run ruff format

lint:
	cd backend && uv run ruff check --fix

typecheck:
	cd backend && uv run ty check

sync:
	git pull --rebase origin master

clean:
	cd backend && rm -rf .pytest_cache htmlcov .coverage .ruff_cache
	cd frontend && rm -rf dist node_modules/.vite
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev-up:
	docker compose up -d postgres

dev-down:
	docker compose stop postgres

db-up: dev-up

db-down: dev-down

db-migrate:
	cd backend && uv run alembic upgrade head

db-revision:
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

db-seed:
	cd backend && uv run python -m scripts.seed

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

fe-install:
	cd frontend && npm ci

fe-dev:
	cd frontend && npm run dev

fe-build:
	cd frontend && npm run build

fe-lint:
	cd frontend && npm run lint

fe-preview:
	cd frontend && npm run preview

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-build:
	docker compose build backend

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# ---------------------------------------------------------------------------
# Azure Container Apps
# ---------------------------------------------------------------------------
# Requires: az CLI (az login), GITHUB_TOKEN env var (PAT: write:packages + read:packages)
# Resource group: budget-tracker-rg  |  App: budget-tracker

azure-provision:
	bash scripts/azure-provision.sh

azure-teardown:
	bash scripts/azure-teardown.sh

deploy:
	bash scripts/azure-deploy.sh

deploy-frontend:
	bash scripts/azure-deploy-frontend.sh

deploy-logs:
	az containerapp logs show \
		--name budget-tracker \
		--resource-group budget-tracker-rg \
		--follow

deploy-status:
	az containerapp show \
		--name budget-tracker \
		--resource-group budget-tracker-rg \
		--query "{status:properties.runningStatus, revisionFqdn:properties.latestRevisionFqdn, url:properties.configuration.ingress.fqdn}" \
		--output table