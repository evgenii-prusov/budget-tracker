# Plan: Block Account Deletion if Postings Exist

## Goal
Update the account deletion logic to prevent accidental data loss by blocking deletion if the account has any associated postings (expenses or incomes). This addresses the "Account Deletion is Asymmetric" concern from the Senior Engineer Code Review.

## Rationale
Currently, deleting an account cascades and deletes all its postings (`cascade="all, delete-orphan"` in `orm.py`), but blocks if there are transfers. This asymmetry can lead to accidental loss of expense history. Making both consistent (blocking) is safer.

## Implementation Steps

### 1. Update Domain Exceptions
**File:** `backend/app/domain/exceptions.py`
*   Add `AccountHasPostingsError` (similar to `AccountHasTransfersError`).

### 2. Update Repository Interface
**File:** `backend/app/service_layer/abstract_repository.py`
*   Add `count_postings_for_account(self, account_id: str) -> int` to `AbstractRepository`.

### 3. Update Repository Implementation
**File:** `backend/app/adapters/repository.py`
*   Implement `count_postings_for_account` in `SqlAlchemyRepository` using a count query.

### 4. Update Service Layer
**File:** `backend/app/service_layer/services.py`
*   In `delete_account`:
    *   Call `uow.repo.count_postings_for_account(account_id)`.
    *   If count > 0, raise `AccountHasPostingsError`.
*   *Note:* The ORM cascade configuration in `orm.py` can remain as a safety net or be removed. Keeping it ensures that if we *force* delete (e.g. via admin tool), it cleans up correctly. But the service layer will prevent it for normal users.

### 5. Update API Router
**File:** `backend/app/api/routers/accounts.py`
*   Catch `AccountHasPostingsError` in `delete_account_endpoint`.
*   Return 409 Conflict.

### 6. Update Tests
**File:** `backend/tests/unit/test_services.py`
*   Update `FakeRepository` to implement `count_postings_for_account`.
*   Add test case: `test_delete_account_with_postings_raises_error`.
*   Update/Remove existing test `test_delete_account_with_postings_succeeds`.

## Verification
*   Run `make test` to ensure new constraints are enforced.
