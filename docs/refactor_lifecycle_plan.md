# Plan: Refactor Application Lifecycle and Database Initialization

## Goal
Decouple database initialization from module import time by implementing FastAPI's `lifespan` context manager. This addresses the "Dependency Module Does Too Much" issue identified in the Senior Engineer Code Review.

## Rationale
Currently, `backend/app/api/dependencies.py` executes database connection logic and schema creation immediately upon import. This causes:
1.  **Side Effects**: Importing the module triggers DB connections, making unit testing difficult without mocking globals.
2.  **Configuration Rigidity**: The database URL is hardcoded.
3.  **Deployment Risks**: DDL statements (`create_all`) run automatically on start, which is not suitable for production.

## Implementation Steps

### 1. Configuration Management
**File:** `backend/app/core/config.py` (New)
*   Create a simple configuration management module.
*   Use `os.getenv` to allow `DATABASE_URL` override (defaulting to existing SQLite file).

### 2. Database Module
**File:** `backend/app/core/db.py` (New)
*   Define a singleton-like structure for `engine` and `session_factory` that is initialized *explicitly*, not at import time.
*   Move `_ensure_mappers_started` logic here, but rename to `init_db`.

### 3. FastAPI Lifespan
**File:** `backend/app/main.py`
*   Define a `lifespan(app: FastAPI)` async context manager.
*   Inside `lifespan`:
    *   Call `init_db()` to configure the engine and start mappers.
    *   Create tables (temporary solution until Alembic is added).
    *   Yield control to the application.
    *   Dispose of the engine on shutdown.
*   Pass `lifespan` to `FastAPI()` constructor.

### 4. Refactor Dependencies
**File:** `backend/app/api/dependencies.py`
*   Remove global `engine` creation and `metadata.create_all`.
*   Update `get_db_session` to use the initialized `session_factory` from `app.core.db`.

## Verification
*   **Tests**: Run `make test` to ensure no regressions.
*   **Manual**: Verify the application starts successfully with `make run`.
*   **Check**: Verify `import app.api.dependencies` in a python shell does *not* create a database file or print SQL logs.
