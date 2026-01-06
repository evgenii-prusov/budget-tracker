# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Budget Tracker is a personal finance application for tracking income, expenses, and transfers across multiple accounts and currencies. The project is organized as a **monorepo** with separate backend and frontend directories.

- **Backend**: Python 3.14+, FastAPI, SQLAlchemy with clean architecture
- **Frontend**: Placeholder for future React/Vue implementation

## Project Structure

```
budget-tracker/
├── backend/                    # Python FastAPI backend
│   ├── app/                    # Main application package
│   │   ├── main.py             # FastAPI endpoints
│   │   ├── model.py            # Domain models
│   │   ├── db.py               # Database schema
│   │   ├── repository.py       # Repository pattern
│   │   ├── schemas.py          # Pydantic schemas
│   │   └── services.py         # Business logic
│   ├── tests/                  # Test suite
│   ├── pyproject.toml          # Backend dependencies
│   ├── Makefile                # Backend-specific commands
│   └── budget.db               # SQLite database
├── frontend/                   # Frontend (placeholder)
├── docs/                       # Documentation
├── .agent/workflows/           # Agent workflows
├── .github/workflows/          # CI/CD
├── .pre-commit-config.yaml     # Pre-commit hooks
├── Makefile                    # Root commands (delegates to backend)
└── CLAUDE.md                   # This file
```

## Development Commands

The project provides two ways to run commands:
1. **Root Makefile** - Run from project root (recommended)
2. **Backend Makefile** - Run from `backend/` directory

### Makefile Commands (from project root)

```bash
# Install dependencies
make install         # Equivalent to: cd backend && uv sync

# Run the application
make run            # Start FastAPI development server

# Testing
make test           # Run all tests
make test-verbose   # Run tests with verbose output
make coverage       # Run tests with terminal coverage report
make coverage-html  # Generate HTML coverage report (opens at backend/htmlcov/index.html)

# Code Quality
make quality        # Run pre-commit checks on all files
make format         # Format code with ruff
make lint           # Lint and auto-fix with ruff

# Git Operations
make sync           # Pull and rebase with master branch

# Cleanup
make clean          # Remove generated files (__pycache__, .coverage, etc.)

# Help
make help           # Show all available commands
```

### Environment Setup
```bash
# Install dependencies (from project root)
make install
# Or from backend directory:
cd backend && uv sync

# Activate virtual environment
source backend/.venv/bin/activate
```

### Running Tests (Direct Commands)

For most testing needs, use the Makefile commands above. For more control:

```bash
# From backend directory:
cd backend

# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run tests with coverage (terminal report)
uv run pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_api.py

# Run specific test function
uv run pytest tests/test_api.py::test_get_accounts
```

### Code Quality (Direct Commands)

For most code quality needs, use `make quality`, `make format`, or `make lint`. For more control:

```bash
# From backend directory:
cd backend

# Run pre-commit checks on all files
uv run pre-commit run --all-files

# Format code with ruff
uv run ruff format

# Lint and auto-fix with ruff
uv run ruff check --fix

# Type check with ty
uv run ty check <file.py>
```

### Running the Application
```bash
# From project root
make run

# Or from backend directory
cd backend && uv run fastapi dev app/main.py

# Access API documentation
# Navigate to http://localhost:8000/docs after starting the server
```

## Architecture Overview

### Domain-Driven Design

The codebase follows a clean architecture pattern with clear separation between domain logic, persistence, and API layers:

- **Domain Layer** (`model.py`): Pure Python domain entities (`Account`, `Entry`) with business logic. No framework dependencies.
- **Persistence Layer** (`db.py`, `repository.py`): SQLAlchemy imperative mapping pattern. The `start_mappers()` function maps domain entities to database tables without polluting domain models with ORM concerns.
- **API Layer** (`main.py`): FastAPI endpoints with Pydantic validation. Uses dependency injection for database sessions.

### Key Architectural Patterns

**Imperative Mapping (SQLAlchemy)**
- Domain models are pure Python classes in `model.py`
- Database schema is defined in `db.py` using SQLAlchemy Core tables
- `start_mappers()` function creates the mapping between domain and persistence
- This keeps domain logic independent of database concerns

**Repository Pattern**
- `AbstractRepository` defines the interface for data access
- `SqlAlchemyRepository` implements persistence using SQLAlchemy sessions
- Allows easy testing by swapping implementations

**Entry Sign Convention**
- Entries store amounts with their actual sign (positive or negative)
- `Account.record_entry()` handles sign logic automatically:
  - EXPENSE: amount becomes negative
  - INCOME: amount becomes positive
  - TRANSFER: amount preserved as-is (caller controls sign)
- Transfer function uses negative debit amounts to decrease source balance

### Database Constraints

- Accounts have unique names per schema (enforced at DB level)
- Entries have foreign keys to accounts with cascade delete
- Initial balance checking prevents negative account balances

## Testing Patterns

### Test Structure
Tests follow the Arrange-Act-Assert pattern with clear comments:
```python
def test_example(session, fixture):
    # 1. Arrange: Prepare data
    # 2. Act: Execute the operation
    # 3. Assert: Verify the outcome
```

### Key Fixtures (see `backend/tests/conftest.py`)
- `session`: In-memory SQLite database session, cleaned up after each test
- `acc_eur`: EUR account with 35.00 initial balance
- `acc_rub`: RUB account with 0.00 initial balance
- `client`: FastAPI test client with session override

### Testing Database Code
The test suite properly handles ORM mapper lifecycle:
- Disposes and restarts mappers for each test to avoid conflicts
- Uses in-memory SQLite with StaticPool for thread safety
- Creates fresh schema for each test

## Domain Concepts

### Transaction Types
- **EXPENSE**: Money going out (decreases account balance)
- **INCOME**: Money coming in (increases account balance)
- **TRANSFER**: Money moving between accounts (supports multi-currency with exchange rates)

### Multi-Currency Support
- Each account has a fixed currency
- Transfers between different currencies require both debit and credit amounts
- Exchange rate is calculated and stored: `credit_amt / debit_amt`

### Business Rules
- Account balances cannot go negative (raises `InsufficientFundsError`)
- Transfer amounts must be positive (function negates debit internally)
- Account names must be unique
- Account currency uses ISO 4217 codes (validated against `VALID_CURRENCIES` set)

### Projects (Planned Feature)
The specification includes project-based expense tracking for events like:
- Business trips
- Vacations
- Home renovations
Each transaction can optionally link to one project for grouped reporting.

## Code Style

### Ruff Configuration
- Line length: 89 characters
- E501 (line length) checking is enabled
- Auto-fixing is enabled for pre-commit hooks

### Pre-commit Hooks
The repository uses pre-commit with hooks that run on `backend/` files:
1. **ruff-check**: Linting with auto-fix
2. **ruff-format**: Code formatting
3. **pytest**: Runs full test suite (must pass before commit)
4. **ty check**: Type checking on modified Python files

### Decimal Usage Guidelines

**Always use `Decimal(0)` instead of `Decimal("0")` for consistency.**

This codebase enforces strict Decimal types for all monetary values to prevent floating-point precision issues. When creating Decimal instances:

- **For integer literals**: Use `Decimal(0)`, `Decimal(100)`, etc.
  - More idiomatic Python
  - Clearer intent (you're converting an integer)
  - Consistent with the rest of the codebase

- **For variables that might be float**: Use `Decimal(str(value))`
  - Required when the source value is a float (to avoid precision loss)
  - The domain layer enforces this with TypeError validation

**Examples:**
```python
# Correct - Default parameters and literal integers
initial_balance: Decimal = Decimal(0)
amount = Decimal(100)

# Correct - Converting potentially unsafe types
user_input = "123.45"
amount = Decimal(user_input)

float_value = 123.45
amount = Decimal(str(float_value))  # Convert to string first

# Incorrect - Inconsistent style
initial_balance: Decimal = Decimal("0")  # Use Decimal(0) instead

# Incorrect - Float precision loss
amount = Decimal(123.45)  # Use Decimal(str(123.45)) or Decimal("123.45")
```

**Rationale:**
- `Decimal(0)` and `Decimal("0")` are functionally equivalent, but using integer literals is more Pythonic for known integer values
- This convention prevents inconsistencies between production code, test code, and API layer
- The domain layer validates all monetary values are Decimal instances at runtime (see `model.py`)

## Important File Locations

- Domain models: `backend/app/model.py`
- Database schema: `backend/app/db.py`
- Repository pattern: `backend/app/repository.py`
- API endpoints: `backend/app/main.py`
- Pydantic schemas: `backend/app/schemas.py`
- Service layer: `backend/app/services.py`
- Test configuration: `backend/tests/conftest.py`
- Product specification: `docs/SPECIFICATION.md` (comprehensive domain details)
- Pre-commit config: `.pre-commit-config.yaml`
- Backend dependencies: `backend/pyproject.toml` (managed by uv)

## Technology Stack

- **Language**: Python 3.14+
- **Web Framework**: FastAPI with standard extras
- **ORM**: SQLAlchemy 2.0+ (imperative mapping)
- **Database**: SQLite (file-based: `backend/budget.db`)
- **Package Manager**: uv
- **Testing**: pytest with pytest-sugar and pytest-cov
- **Code Coverage**: pytest-cov (run coverage commands to see current overall coverage)
- **Linting/Formatting**: ruff
- **Type Checking**: ty
- **Validation**: Pydantic (via FastAPI)

## CI/CD Integration

The repository includes GitHub workflows for Claude Code integration:
- `claude.yml`: Claude Code workflow triggered by @claude mentions
- `claude-code-review.yml`: Automated code review workflow

## Agent Workflows

Located in `.agent/workflows/`:
- `pre-commit.md`: Runs pre-commit checks
- `start-feature.md`: Creates feature branches from master
- `feature-development.md`: Complete feature development workflow from branch creation to PR merge

## Future Features (See docs/SPECIFICATION.md)

The specification outlines extensive planned functionality including:
- Multi-account tracking with multiple currencies
- Invoice OCR scanning
- Budget management per category
- Project-based expense tracking
- Spending reports and analytics
- AI assistant integration (MCP server)

Refer to `docs/SPECIFICATION.md` for detailed domain model, business rules, and feature specifications.
