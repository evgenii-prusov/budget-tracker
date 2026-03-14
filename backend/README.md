# Budget Tracker Backend

FastAPI backend for the Budget Tracker application.

## Quick Start (Dev Mode)

Dev mode runs the backend locally (with hot reload) against a Dockerised Postgres.
This is the right mode for day-to-day development.

```bash
# Install dependencies
uv sync

# Start Postgres only (no backend container)
make dev-up

# Run migrations
make db-migrate

# Run development server (hot reload)
make run
```

> **Important:** use `make dev-up` (not `make docker-up`) for dev. `docker-up` also
> starts a backend container that will conflict with `make run` on port 8000.

## Database

The app uses PostgreSQL. A Docker Compose file is provided at the project root.

```bash
# Start Postgres (dev)
make dev-up

# Run migrations
make db-migrate

# Create a new migration after model changes
make db-revision msg="add foo column"

# Stop Postgres
make dev-down
```

Copy `.env.example` to `.env` and adjust if needed:
```
DATABASE_URL=postgresql://budget:budget@localhost:5432/budget_tracker
API_KEY=change-me
```

## Production (Docker)

Prod mode runs everything in Docker — Postgres and the backend container together.
Use this for production deployments or to test the built image locally.

### Prerequisites

- Docker and Docker Compose installed
- An `API_KEY` value chosen for authenticating API requests

### First-time setup

```bash
# From the repo root -- export your API key
export API_KEY=your-secret-key

# Build the backend image
make docker-build

# Start Postgres and the backend (runs migrations automatically)
make docker-up
```

The backend will be available at `http://localhost:8000`.
Pass the API key in every request via the `Authorization: Bearer <token>` header.

### Day-to-day commands

```bash
# Start all services
make docker-up

# Stop and remove all services (data is preserved in the postgres volume)
make docker-down

# Tail logs
make docker-logs

# Rebuild after code changes, then restart
make docker-build && make docker-up
```

### Switching back to dev mode

```bash
# Stop all Docker services (including the backend container)
make docker-down

# Start only Postgres, then run the local server
make dev-up
make run
```

### Passing configuration

All runtime configuration is provided through environment variables.
The `docker-compose.yml` reads them from the host shell:

| Variable       | Required | Default | Description                                       |
|----------------|----------|---------|---------------------------------------------------|
| `API_KEY`      | Yes      | (none)  | Secret key for `Authorization: Bearer` auth        |
| `LOG_LEVEL`    | No       | `INFO`  | Python log level (`DEBUG`, `INFO`, `WARNING`, etc.)|

`DATABASE_URL` is set automatically inside `docker-compose.yml` — no extra
configuration is needed for it when using Docker Compose.

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
- `API_KEY` **(required)**: Secret key that clients must pass in the `Authorization: Bearer <token>` header
- `LOG_LEVEL`: Python logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`). Default: `INFO`
