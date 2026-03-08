.PHONY: help run test test-verbose coverage coverage-html quality format lint typecheck sync install clean db-up db-down db-migrate db-revision docker-build docker-up docker-down docker-logs

help:
	@echo "Budget Tracker - Available Commands"
	@echo "===================================="
	@echo "make install       - Install all dependencies"
	@echo "make run           - Start backend server"
	@echo "make test          - Run all tests"
	@echo "make test-verbose  - Run tests with verbose output"
	@echo "make coverage      - Run tests with coverage report"
	@echo "make coverage-html - Run tests with HTML coverage report"
	@echo "make quality       - Run prek checks on all files"
	@echo "make format        - Format code with ruff"
	@echo "make lint          - Lint and auto-fix with ruff"
	@echo "make typecheck     - Run ty type checker"
	@echo "make sync          - Sync with remote master branch"
	@echo "make clean         - Remove generated files"
	@echo ""
	@echo "Development database"
	@echo "make db-up         - Start Postgres (dev)"
	@echo "make db-down       - Stop Postgres (dev)"
	@echo "make db-migrate    - Run Alembic migrations"
	@echo "make db-revision   - Create new migration (msg=\"description\")"
	@echo ""
	@echo "Docker (production)"
	@echo "make docker-build  - Build the backend Docker image"
	@echo "make docker-up     - Start Postgres + backend via Docker Compose"
	@echo "make docker-down   - Stop and remove Docker Compose services"
	@echo "make docker-logs   - Tail logs from all Docker Compose services"

install:
	cd backend && uv sync

run:
	cd backend && uv run fastapi dev app/main.py

test:
	cd backend && uv run pytest

test-verbose:
	cd backend && uv run pytest -v

coverage:
	cd backend && uv run pytest --cov=app --cov-report=term-missing

coverage-html:
	cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated at backend/htmlcov/index.html"

quality:
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
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

db-up:
	cd backend && make db-up

db-down:
	cd backend && make db-down

db-migrate:
	cd backend && make db-migrate

db-revision:
	cd backend && make db-revision msg="$(msg)"

docker-build:
	docker compose build backend

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
