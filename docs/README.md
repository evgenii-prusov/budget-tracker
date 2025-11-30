# Budget Tracker - AI Context

> This file provides context for AI coding assistants (Claude, Cursor, Copilot, etc.)

## Project Overview

Budget Tracker is a personal finance application for tracking income, expenses, and transfers across multiple accounts and currencies.

## Tech Stack

- **Backend:** Python 3.14+, Django 5.x, Django Ninja (API)
- **Database:** PostgreSQL 16
- **Cache/Queue:** Redis, Celery
- **Storage:** MinIO (S3-compatible)
- **OCR:** Tesseract (pytesseract)
- **Frontend:** Django Templates + HTMX + Tailwind CSS
- **Infrastructure:** Docker Compose (dev), Kubernetes + Helm (prod)

## Project Structure

```plaintext
src/
├── config/              # Django project settings
│   ├── settings/        # Split settings (base, local, test, production)
│   ├── urls.py
│   ├── celery.py
│   └── api.py           # Django Ninja API setup
├── apps/
│   ├── users/           # Custom user model, auth
│   ├── accounts/        # Financial accounts (bank, cash, etc.)
│   ├── categories/      # Transaction categories
│   ├── transactions/    # Income, expenses, transfers
│   ├── invoices/        # Receipt uploads + OCR
│   └── budgets/         # Budget tracking
├── core/                # Shared utilities
│   ├── models.py        # Base models (TimestampedModel, UserScopedModel)
│   ├── storage.py       # MinIO/S3 integration
│   └── exceptions.py    # Custom exceptions
└── templates/           # Django templates
```

## Key Patterns

### Multi-Tenancy

All data is scoped to a user. Every model inherits from `UserScopedModel` which has a `user` foreign key. All queries must filter by `user=request.user`.

```python
class UserScopedModel(TimestampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    
    class Meta:
        abstract = True
```

### API Style (Django Ninja)

We use Django Ninja with Pydantic schemas:

```python
from ninja import Router, Schema

router = Router()

class TransactionOut(Schema):
    id: int
    amount: Decimal
    # ...

@router.get("/", response=list[TransactionOut])
def list_transactions(request):
    return request.user.transactions.all()
```

### Transaction Types

- `income`: Money coming in → adds to account balance
- `expense`: Money going out → subtracts from account balance  
- `transfer`: Money between accounts → subtracts from source, adds to destination

### Multi-Currency

- Each account has a fixed currency
- Transfers between currencies require exchange rate
- Reports convert to user's default currency

## Coding Standards

- **Type hints:** Required on all functions
- **Docstrings:** Required on all public functions/classes
- **Testing:** pytest, aim for >80% coverage
- **Linting:** ruff (replaces flake8, isort, black)
- **Type checking:** mypy with strict mode

## Common Commands

```bash
# Development
uv sync                              # Install dependencies
uv run python src/manage.py runserver   # Run dev server
uv run pytest                        # Run tests
uv run ruff check src/               # Lint
uv run mypy src/                     # Type check

# Docker
docker compose -f docker/docker-compose.yml up   # Start all services

# Migrations
uv run python src/manage.py makemigrations
uv run python src/manage.py migrate
```

## Key Documentation

- `docs/SPECIFICATION.md` - Full product specification
- `docs/architecture/DATA_MODEL.md` - Database design
- `docs/architecture/API.md` - API design

## Current Status

Phase: MVP Development
Focus: Core transaction management + multi-currency support

## Important Notes

1. **Always filter by user:** Never return data without filtering by the authenticated user
2. **Decimal for money:** Always use `Decimal`, never `float` for monetary values
3. **UTC timestamps:** Store all times in UTC, convert for display
4. **Soft deletes:** Use `is_active` flag instead of hard deletes where possible
