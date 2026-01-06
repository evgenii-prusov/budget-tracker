.PHONY: help run test test-verbose coverage coverage-html quality format lint install clean

help:
	@echo "Budget Tracker Backend - Available Commands"
	@echo "============================================"
	@echo "make install       - Install dependencies with uv"
	@echo "make run           - Start FastAPI development server"
	@echo "make test          - Run all tests"
	@echo "make test-verbose  - Run tests with verbose output"
	@echo "make coverage      - Run tests with coverage report"
	@echo "make coverage-html - Run tests with HTML coverage report"
	@echo "make quality       - Run pre-commit checks on all files"
	@echo "make format        - Format code with ruff"
	@echo "make lint          - Lint and auto-fix with ruff"
	@echo "make clean         - Remove generated files"

install:
	uv sync

run:
	uv run fastapi dev app/main.py

test:
	uv run pytest

test-verbose:
	uv run pytest -v

coverage:
	uv run pytest --cov=app --cov-report=term-missing

coverage-html:
	uv run pytest --cov=app --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated at htmlcov/index.html"

quality:
	uv run pre-commit run --all-files

format:
	uv run ruff format

lint:
	uv run ruff check --fix

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
