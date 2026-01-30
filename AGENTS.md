# Repository Guidelines

## Project Structure & Module Organization
- `backend/app/`: FastAPI application code. Key areas include `api/routers/` for HTTP endpoints, `domain/` for core models/exceptions, `service_layer/` for business logic, and `adapters/` for persistence/integration.
- `backend/tests/`: Test suite organized by `unit/`, `integration/`, and `e2e/`.
- `docs/`: Specifications and engineering plans.
- `htmlcov/`: Generated coverage reports (do not edit by hand).
- `frontend/`: Currently empty placeholder directory.

## Build, Test, and Development Commands
Use the root Makefile for common tasks (it delegates into `backend/`). Examples:
- `make install`: Install backend dependencies with `uv`.
- `make run`: Start the FastAPI dev server (`uv run fastapi dev app/main.py`).
- `make test`: Run the full pytest suite.
- `make coverage`: Run tests with coverage in the terminal.
- `make coverage-html`: Generate an HTML report at `backend/htmlcov/index.html`.
- `make format`: Format Python with Ruff.
- `make lint`: Lint and auto-fix with Ruff.

## Coding Style & Naming Conventions
- Python target version is 3.12 (see `backend/pyproject.toml`).
- Formatting and linting are handled by Ruff (`ruff format`, `ruff check --fix`).
- Use snake_case for modules/functions/variables; tests follow `test_*.py` naming.
- Keep line length to 89 characters to match Ruff configuration.

## Testing Guidelines
- Framework: `pytest` with `pytest-cov`.
- Tests live under `backend/tests/` with clear unit/integration/e2e separation.
- Run `make test` locally before opening a PR; use `make coverage` when changing core logic.

## Commit & Pull Request Guidelines
- Commit messages follow a lightweight type prefix seen in history, e.g. `feat:`, `fix:`, `refactor:`, `test:`.
- PRs should include: a concise summary, tests run, and any relevant docs updates.
- If your change impacts data models or persistence, call it out explicitly in the PR description.

## Configuration Notes
- `DATABASE_URL` controls the SQLAlchemy connection string (defaults to SQLite).
- `LOG_LEVEL` sets logging verbosity (default `INFO`).
