# Budget Tracker

Personal finance application for tracking income, expenses, and transfers.

<!-- [![CI](https://github.com/evgenii-prusov/budget-tracker/actions/workflows/ci.yml/badge.svg)](...) -->
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](...)

## Features

- Multi-account tracking (bank, cash, credit cards)
- Multi-currency support
- Invoice OCR scanning
- Budget management
- Spending reports
- **AI Assistant Integration** - MCP server for Claude/AI assistants
- **Telegram Bot** - Communication channel complimenting the app

## Quick Start

**Development (local)**

```bash
git clone ...  # TODO: Add repo URL
cd budget-tracker
make install
make run
```

**Production (Docker)**

```bash
export API_KEY=your-secret-key
make docker-up          # starts Postgres + backend, runs migrations
```

The API will be available at `http://localhost:8000`.  
See [backend/README.md](./backend/README.md#production-docker) for full Docker documentation.

To run tests:

```bash
make test
```

## Documentation

See [docs/](./docs/) for full documentation.

## Tech Stack

Python 3.12, FastAPI, SQLAlchemy, pytest, Ruff, uv
