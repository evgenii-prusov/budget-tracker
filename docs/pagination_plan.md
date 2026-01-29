# Plan: Implement Pagination for List Endpoints

## Goal
Add pagination (skip/limit) to all list endpoints to improve performance and scalability, as recommended in the Senior Engineer Code Review.

## Implementation Steps

### 1. Update Repository Interface
**File:** `backend/app/service_layer/abstract_repository.py`
*   Update `list_all(self)` to `list_all(self, skip: int = 0, limit: int = 100)`
*   Update `list_transfers(self)` to `list_transfers(self, skip: int = 0, limit: int = 100)`
*   Update `list_postings(self, account_id: str | None = None)` to `list_postings(self, account_id: str | None = None, skip: int = 0, limit: int = 100)`
*   Update `list_categories(self)` to `list_categories(self, skip: int = 0, limit: int = 100)`

### 2. Update Repository Implementation
**File:** `backend/app/adapters/repository.py`
*   Implement `skip` and `limit` using SQLAlchemy's `offset()` and `limit()` methods in `SqlAlchemyRepository`.

### 3. Update Service Layer
**File:** `backend/app/service_layer/services.py`
*   Update `list_accounts` (if it exists as a service function, currently it's called directly on repo in router) or verify usage.
    *   *Correction*: `list_accounts` is called directly on `uow.repo` in the router. I should consider adding a wrapper service or just updating the router to call the repo with parameters.
    *   I will verify if I should expose `list_accounts` via `services.py` for consistency. The current code uses `uow.repo.list_all()` directly in the router.
*   Update `list_transfers`, `list_postings`, `list_categories` in `services.py` to accept and pass `skip` and `limit`.

### 4. Update API Routers
**Files:**
*   `backend/app/api/routers/accounts.py`
*   `backend/app/api/routers/categories.py`
*   `backend/app/api/routers/postings.py`
*   `backend/app/api/routers/transfers.py`

*   Add `skip: int = Query(0, ge=0)` and `limit: int = Query(50, ge=1, le=100)` parameters to list endpoints.
*   Pass these parameters to the service layer (or repository).

### 5. Update Tests
**Files:**
*   `backend/tests/unit/test_services.py` (Update FakeRepository to handle or ignore skip/limit, or implement slicing)
*   `backend/tests/integration/test_repository.py` (Test pagination logic with real DB)
*   `backend/tests/e2e/test_api.py` (Test API parameters)

## Verification
*   Run `make test` to ensure all tests pass.
