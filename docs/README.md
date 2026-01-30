# Budget Tracker - AI Context

> This file provides context for AI coding assistants (Claude, Cursor, Copilot, etc.)

## Project Overview

Budget Tracker is a personal finance application for tracking income, expenses, transfers, and
balances across multiple accounts and currencies.

## Tech Stack

- **Backend:** Python 3.12, FastAPI
- **Persistence:** SQLAlchemy + SQLite (default)
- **Frontend:** React + TypeScript + Tailwind (Vite)
- **Tooling:** pytest, Ruff, uv

## Project Structure

```plaintext
backend/
  app/
    api/routers/        # FastAPI endpoints
    domain/             # Core models/exceptions
    service_layer/      # Business logic
    adapters/           # ORM + repository
  tests/                # pytest suite
frontend/
  src/                  # React app
```

## Key Domain Rules

- **Posting types:** `INCOME` or `EXPENSE`.
- **Amounts:** Always `Decimal` in the domain. Expenses are stored as negative amounts.
- **Balances:**
  `balance = initial_balance + sum(postings) - outgoing_transfers + incoming_transfers`
- **Currencies:** Each account has a fixed currency.

## Common Commands

```bash
# Install dependencies (backend + frontend)
make install

# Run backend + frontend together (foreground, Ctrl+C to stop)
make run-all

# Run backend or frontend only
make run-backend
make run-frontend

# Start/stop both in background
make start
make stop

# Tests
make test
```

## Frontend Notes

- Dev server runs on `http://localhost:5173`.
- Backend runs on `http://localhost:8000`.
- Vite proxy forwards `/api/*` to backend during dev.

## Configuration Notes

- `DATABASE_URL` controls the SQLAlchemy connection string (defaults to SQLite).
- `LOG_LEVEL` sets logging verbosity (default `INFO`).

## Current Status

- MVP: Accounts, Categories, Postings, Transfers (backend + UI)
