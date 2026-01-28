# Budget Tracker

## Project Overview

Budget Tracker is a personal finance application designed for tracking income, expenses, and transfers across multiple accounts and currencies.

**Key Features:**
*   Multi-account & Multi-currency support.
*   Invoice OCR scanning (planned).
*   Clean Architecture / DDD approach.
*   Python 3.14+ backend with FastAPI.

## Architecture

The project follows a **Clean Architecture** (Hexagonal) pattern with strict layer separation:

1.  **Domain (`backend/app/domain`)**: Pure Python entities (`Account`, `Posting`, `Transfer`) and business logic. No external dependencies.
2.  **Service Layer (`backend/app/service_layer`)**: Application use cases (`services.py`) and repository interfaces (`abstract_repository.py`). Orchestrates domain objects.
3.  **Adapters (`backend/app/adapters`)**: Infrastructure implementations (`orm.py`, `repository.py`). Maps domain objects to the database (SQLAlchemy Imperative Mapping).
4.  **API (`backend/app/api`)**: Interface layer (`routers`, `schemas`). Handles HTTP requests/responses using FastAPI and Pydantic.

## Tech Stack

*   **Language:** Python 3.14+
*   **Framework:** FastAPI
*   **Database:** SQLite (file-based)
*   **ORM:** SQLAlchemy 2.0+ (Imperative Mapping)
*   **Package Manager:** `uv`
*   **Testing:** `pytest`
*   **Linting/Formatting:** `ruff`
*   **Type Checking:** `ty`

## Development Workflow

**IMPORTANT:** Always use the `make` commands provided in the root directory.

### Setup & Run
*   **Install Dependencies:** `make install` (uses `uv sync` in backend)
*   **Start Server:** `make run` (starts FastAPI dev server)
*   **Sync with Master:** `make sync`

### Testing
*   **Run All Tests:** `make test`
*   **Verbose Output:** `make test-verbose`
*   **Coverage Report:** `make coverage` (terminal) or `make coverage-html` (HTML report)

### Code Quality
*   **Run All Checks:** `make quality` (runs pre-commit hooks: lint, format, test, type check)
*   **Format Code:** `make format` (ruff)
*   **Lint Code:** `make lint` (ruff check --fix)

## Coding Conventions

### 1. Decimal Usage (Monetary Values)
*   **Strictly use `Decimal`** for all monetary values.
*   **Integer Literals:** Use `Decimal(0)`, `Decimal(100)` (preferred over `Decimal("0")`).
*   **Float Conversion:** Use `Decimal(str(float_val))` to avoid precision loss.
*   **Domain Validation:** The domain layer validates `Decimal` types.

### 2. Architecture Rules
*   **Domain Purity:** Domain models must NOT depend on ORM or API types.
*   **Imperative Mapping:** Database tables are defined in `adapters/orm.py` and mapped to domain classes.
*   **Repository Pattern:** Use `AbstractRepository` in services; inject `SqlAlchemyRepository` at runtime.

### 3. Testing
*   **Pattern:** Arrange-Act-Assert.
*   **Database:** Tests use an in-memory SQLite database with `StaticPool` (recreated per test).
*   **Fixtures:** Use `session` (DB session), `client` (FastAPI client), `acc_eur`/`acc_rub` (pre-configured accounts).

### 4. Git
*   **Commit Messages:** clear, concise, "why" over "what".
*   **No Co-Authors:** Do not add `Co-Authored-By` lines.

### 5. Variable Naming (Service Layer)
*   **Standard Retrieval:** Use the simple entity name (e.g., `account`, `category`) when retrieving an object by its ID for actions or return.
*   **Duplicate Check:** Use `existing_<entity_name>` (e.g., `existing_account`) specifically when checking for name collisions during creation.

### 6. Import Style
*   **Explicit Imports:** Use explicit imports over module imports where possible.
*   **One per Line:** Put each import on its own line (e.g., `from module import A` and `from module import B`, not `from module import A, B`).
*   **Order:** Standard library, then third-party, then local application imports.

## Directory Structure

*   `backend/`: Python backend source code.
    *   `app/`: Main application package.
    *   `tests/`: Test suite (`unit`, `integration`, `e2e`).
    *   `pyproject.toml`: Dependency definitions.
*   `docs/`: Documentation and Specifications (`SPECIFICATION.md`).
*   `.agent/`: Agent workflows.
