# Budget Tracker Backend

FastAPI backend for the Budget Tracker application.

## Quick Start

```bash
# Install dependencies
uv sync

# Start Postgres
make db-up

# Run migrations
make db-migrate

# Run development server
make run
```

## Database

The app uses PostgreSQL. A Docker Compose file is provided at the project root.

```bash
# Start Postgres
make db-up

# Run migrations
make db-migrate

# Create a new migration after model changes
make db-revision msg="add foo column"

# Stop Postgres
make db-down
```

Copy `.env.example` to `.env` and adjust if needed:
```
DATABASE_URL=postgresql://budget:budget@localhost:5432/budget_tracker
```

## Testing

All tests run against a throwaway Postgres container via [testcontainers](https://testcontainers-python.readthedocs.io/). Docker must be running.

```bash
# Run all tests
make test

# Run with coverage
make coverage
```

## Environment Variables

- `DATABASE_URL` **(required)**: PostgreSQL connection URL (e.g., `postgresql://budget:budget@localhost:5432/budget_tracker`)
- `LOG_LEVEL`: Python logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`). Default: `INFO`

See the root `CLAUDE.md` for full documentation.
