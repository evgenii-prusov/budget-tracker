.PHONY: help run test test-verbose coverage coverage-html quality format lint sync install clean

help:
	@echo "Budget Tracker - Available Commands"
	@echo "===================================="
	@echo "make install       - Install all dependencies"
	@echo "make run           - Start backend server"
	@echo "make test          - Run all tests"
	@echo "make test-verbose  - Run tests with verbose output"
	@echo "make coverage      - Run tests with coverage report"
	@echo "make coverage-html - Run tests with HTML coverage report"
	@echo "make quality       - Run pre-commit checks on all files"
	@echo "make format        - Format code with ruff"
	@echo "make lint          - Lint and auto-fix with ruff"
	@echo "make sync          - Sync with remote master branch"
	@echo "make clean         - Remove generated files"

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
	cd backend && uv run pre-commit run --all-files

format:
	cd backend && uv run ruff format

lint:
	cd backend && uv run ruff check --fix

sync:
	git pull --rebase origin master

clean:
	cd backend && rm -rf .pytest_cache htmlcov .coverage .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
