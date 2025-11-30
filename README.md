# Budget Tracker

Personal finance application for tracking income, expenses, and transfers.

<!-- [![CI](https://github.com/evgenii-prusov/budget-tracker/actions/workflows/ci.yml/badge.svg)](...) -->
[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](...)

## Features

- Multi-account tracking (bank, cash, credit cards)
- Multi-currency support
- Invoice OCR scanning
- Budget management
- Spending reports
- **AI Assistant Integration** - MCP server for Claude/AI assistants

## Quick Start

git clone ...  # TODO: Add repo URL
cd budget-tracker
uv sync
docker compose up -d
uv run python src/manage.py migrate
uv run python src/manage.py runserver

## Documentation

See [docs/](./docs/) for full documentation.

## Tech Stack

Python, Django, PostgreSQL, Redis, Kubernetes
