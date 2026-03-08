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
API_KEY=change-me
```

## Production (Docker)

The project ships a production Dockerfile and a `docker-compose.yml` that starts
Postgres and the backend together.

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
# Start services
make docker-up

# Stop services (data is preserved in the postgres volume)
make docker-down

# Tail logs
make docker-logs

# Rebuild after code changes
make docker-build && make docker-up
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
