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

## Quick Start

```bash
git clone ...  # TODO: Add repo URL
cd budget-tracker
make install
make run-all
```

To run backend only:

```bash
make run-backend
```

To run frontend only:

```bash
make run-frontend
```

To start/stop both in the background:

```bash
make start
make stop
```

To run tests:

```bash
make test
```

## Documentation

See [docs/](./docs/) for full documentation.

## Tech Stack

Python 3.12, FastAPI, SQLAlchemy, React, TypeScript, Tailwind, pytest, Ruff, uv

## Docker (optional)

Pros:
- Consistent dev environment across machines (Python/Node/tooling versions).
- One command to run backend + frontend + any future services.
- Easier onboarding for contributors.

Cons:
- Slower local dev feedback loops vs native (especially on macOS).
- Extra maintenance: Dockerfiles, compose files, volumes, cache strategy.
- SQLite-in-container needs careful volume mapping to persist data.

Recommendation:
- If you expect more contributors or additional services (DB, cache, workers), it’s a good time to add Docker Compose.
- If it’s mostly solo dev and fast iteration matters, keep native for now and add Docker later.
