# Budget Tracker Backend

FastAPI backend for the Budget Tracker application.

## Quick Start

```bash
# Install dependencies
uv sync

# Run development server
uv run fastapi dev app/main.py

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=term-missing
```

## Environment Variables

- `DATABASE_URL`: SQLAlchemy database URL. Default: `sqlite:///budget.db`
- `LOG_LEVEL`: Python logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`). Default: `INFO`

See the root `CLAUDE.md` for full documentation.
