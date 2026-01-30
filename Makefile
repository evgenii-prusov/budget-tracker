.PHONY: help install install-backend install-frontend run run-backend run-frontend \
	run-all start start-backend start-frontend stop stop-backend stop-frontend \
	test test-verbose coverage coverage-html quality format lint sync clean

help:
	@echo "Budget Tracker - Available Commands"
	@echo "===================================="
	@echo "make install       - Install backend + frontend dependencies"
	@echo "make run-backend   - Start backend server (foreground)"
	@echo "make run-frontend  - Start frontend dev server (foreground)"
	@echo "make run-all       - Start backend + frontend (foreground)"
	@echo "make start         - Start backend + frontend (background)"
	@echo "make stop          - Stop backend + frontend (background)"
	@echo "make test          - Run all tests"
	@echo "make test-verbose  - Run tests with verbose output"
	@echo "make coverage      - Run tests with coverage report"
	@echo "make coverage-html - Run tests with HTML coverage report"
	@echo "make quality       - Run pre-commit checks on all files"
	@echo "make format        - Format code with ruff"
	@echo "make lint          - Lint and auto-fix with ruff"
	@echo "make sync          - Sync with remote master branch"
	@echo "make clean         - Remove generated files"

RUN_DIR := .run
FRONTEND_PORT ?= 5173

install: install-backend install-frontend

install-backend:
	cd backend && uv sync

install-frontend:
	cd frontend && npm install

run: run-backend

run-backend:
	cd backend && uv run fastapi dev app/main.py

run-frontend:
	cd frontend && npm run dev -- --host --port $(FRONTEND_PORT)

run-all:
	@sh -c 'set -e; trap "kill 0" EXIT; (cd backend && uv run fastapi dev app/main.py) & (cd frontend && npm run dev -- --host --port $(FRONTEND_PORT)) & wait'

start: start-backend start-frontend

start-backend:
	@mkdir -p $(RUN_DIR)
	@sh -c 'cd backend && nohup uv run fastapi dev app/main.py > ../$(RUN_DIR)/backend.log 2>&1 & echo $$! > ../$(RUN_DIR)/backend.pid'
	@echo "Backend started (PID: $$(cat $(RUN_DIR)/backend.pid))"

start-frontend:
	@mkdir -p $(RUN_DIR)
	@sh -c 'cd frontend && nohup npm run dev -- --host --port $(FRONTEND_PORT) > ../$(RUN_DIR)/frontend.log 2>&1 & echo $$! > ../$(RUN_DIR)/frontend.pid'
	@echo "Frontend started (PID: $$(cat $(RUN_DIR)/frontend.pid))"

stop: stop-backend stop-frontend

stop-backend:
	@if [ -f $(RUN_DIR)/backend.pid ]; then \
		kill $$(cat $(RUN_DIR)/backend.pid) && rm -f $(RUN_DIR)/backend.pid; \
		echo "Backend stopped"; \
	else \
		echo "Backend not running"; \
	fi

stop-frontend:
	@if [ -f $(RUN_DIR)/frontend.pid ]; then \
		kill $$(cat $(RUN_DIR)/frontend.pid) && rm -f $(RUN_DIR)/frontend.pid; \
		echo "Frontend stopped"; \
	else \
		echo "Frontend not running"; \
	fi

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
	rm -rf $(RUN_DIR)
