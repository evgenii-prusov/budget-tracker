# Code Review: Category Management Feature

**Reviewer**: Code Maintainer
**Date**: 2026-01-27
**Feature**: Category Management (CRUD for transaction categories)

---

## Summary

This PR adds category management functionality to the Budget Tracker application. Categories can be associated with transactions (postings) for expense/income organization. The implementation follows the project's clean architecture pattern.

**Overall Assessment**: The architecture is sound, but there are critical issues that must be fixed before merging, plus an architectural question to resolve.

---

## Critical Issues (Must Fix Before Merge)

### 1. Broken Test Fixtures

**File**: `backend/tests/conftest.py` (lines 81-109)

The test fixtures still use the old parameter names but the `Posting` class now expects different parameters:

```python
# Current code (BROKEN):
def _make_posting(
    ...
    category: str | None = "test",      # Should be: category_id
    category_type: PostingType = ...,   # Should be: posting_type
) -> Posting:
    return Posting(id, account_id, amount, posting_date, category, category_type)
```

The `Posting` class signature is:
```python
def __init__(self, posting_id, account_id, amount, posting_date, category_id, posting_type):
```

**Impact**: Tests will fail at runtime with TypeError.

**Fix Required**: Rename parameters in `conftest.py`:
- `category` -> `category_id`
- `category_type` -> `posting_type`

Also fix fixtures `posting_1`, `posting_2`, `posting_3` which have the same issue.

---

### 2. No Tests for Category Feature

The Category feature has **zero test coverage**:

| Test Type | Coverage |
|-----------|----------|
| Unit tests (services) | None |
| Integration tests (repository) | None |
| E2E tests (API) | None |

**Required tests to add:**

Unit tests (`test_services.py`):
- `test_create_category_success`
- `test_create_category_duplicate_name_raises_error`
- `test_list_categories_empty`
- `test_list_categories_returns_all`
- `test_delete_category_success`
- `test_delete_category_not_found_raises_error`

E2E tests (`test_api.py`):
- `test_create_category_endpoint`
- `test_create_category_duplicate_returns_409`
- `test_list_categories_endpoint`
- `test_delete_category_endpoint`
- `test_delete_category_not_found_returns_404`

---

## Architectural Issue (Needs Discussion)

### 3. Redundant Type Definitions: PostingType vs CategoryType

Both enums have identical values:

```python
class PostingType(StrEnum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"

class CategoryType(StrEnum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
```

A `Posting` has:
- `posting_type: PostingType` (EXPENSE or INCOME)
- `category_id: str | None` -> links to `Category` which has `category_type`

**Problem**: This creates data redundancy and potential inconsistency. A posting could have `posting_type=EXPENSE` but be linked to an INCOME category.

**Options to consider:**

1. **Remove CategoryType** - Categories are just labels (e.g., "Groceries", "Salary") and can be used for any posting type. The posting_type on the Posting determines income/expense.

2. **Remove PostingType** - Derive the type from the category. BUT this requires categories to be mandatory (not nullable).

3. **Keep both but validate** - When assigning a category to a posting, validate that `posting.posting_type == category.category_type`. Add a constraint or validation logic.

**Recommendation**: Option 1 seems cleanest - categories should just be organizational labels, and the Posting itself determines if money is going in or out.

---

## Code Issues (Should Fix)

### 4. Dead Code - Commented Imports

**File**: `backend/app/api/routers/categories.py` (line 8)
```python
# from app.domain.exceptions import CategoryInUseError
```

**File**: `backend/app/service_layer/services.py` (line 12)
```python
# from app.domain.exceptions import CategoryInUseError # Implemented if needed
```

**Action**: Either remove these comments or implement the feature.

---

### 5. Missing Category-In-Use Validation

**File**: `backend/app/service_layer/services.py` (lines 99-109)

```python
def delete_category(repo: AbstractRepository, *, category_id: str) -> None:
    category = repo.get_category(category_id)
    if category is None:
        raise CategoryNotFoundError(...)

    # Check usage if needed
    # (not implemented in repo yet, assuming safe delete or DB constraint will fail)
    # Ideally we check if any postings use this category.

    repo.delete_category(category)
    repo.commit()
```

The ORM has FK constraint `postings.category_id -> category.category_id`, but behavior on delete is undefined.

**Risk**: Deleting a category that has postings will either:
- Cause a database integrity error (confusing message to user)
- Orphan postings if FK allows NULL on cascade

**Fix**: Add to repository interface:
```python
def count_postings_for_category(self, category_id: str) -> int
```

Then in service:
```python
if repo.count_postings_for_category(category_id) > 0:
    raise CategoryInUseError(f"Category '{category.name}' has postings and cannot be deleted")
```

---

### 6. Missing GET Single Category Endpoint

**File**: `backend/app/api/routers/categories.py`

The accounts router has `GET /accounts/{account_id}`, but categories router is missing the equivalent:

```python
# Missing endpoint:
@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category_endpoint(category_id: str, repo: RepoDep):
    ...
```

**Action**: Add for consistency.

---

### 7. Overly Broad Exception Handling

**File**: `backend/app/api/routers/categories.py` (lines 38-40, 52-54)

```python
except Exception as exc:
    repo.rollback()
    raise HTTPException(status_code=400, detail=str(exc))
```

**Problem**: Catching all `Exception` types can hide bugs and give misleading error codes.

**Compare with accounts router** which handles specific exceptions:
```python
except DuplicateAccountNameError as exc:
    raise HTTPException(status_code=409, detail=str(exc))
except InvalidInitialBalanceError as exc:
    raise HTTPException(status_code=400, detail=str(exc))
```

**Fix**: Remove broad handlers or make them log + re-raise as 500 for unexpected errors.

---

### 8. Inconsistent List Endpoint Pattern

| Router | List Implementation |
|--------|---------------------|
| Accounts | `return repo.list_all()` (direct repo call) |
| Categories | `return list_categories(repo)` (via service) |

**Action**: Standardize. Prefer service layer for consistency with other operations.

---

## Minor Issues

### 9. Decimal Style Inconsistency

**File**: `backend/app/api/schemas.py` (line 25)

```python
initial_balance: Decimal = Decimal("0.0")
```

Per CLAUDE.md: "Always use `Decimal(0)` instead of `Decimal("0")`"

**Fix**: Change to `Decimal(0)`.

---

### 10. CategoryResponse Type Could Be Stricter

**File**: `backend/app/api/schemas.py` (line 43)

```python
category_type: str  # Could be more specific
```

**Better**:
```python
category_type: Literal["INCOME", "EXPENSE"]
```

Provides better API documentation and type safety.

---

## What's Done Well

1. Clean architecture properly followed - domain, service layer, adapters, API properly separated
2. Domain model `Category` has proper `__eq__`, `__hash__`, `__repr__` methods
3. Exception hierarchy is well-organized in `domain/exceptions.py`
4. Repository interface properly abstracted with all CRUD methods
5. Service layer handles duplicate name validation correctly
6. ORM mapper properly configured for Category
7. Pydantic schemas have proper validation constraints

---

## Checklist Before Merge

- [ ] Fix test fixtures in `conftest.py` (Critical)
- [ ] Add unit tests for category services (Critical)
- [ ] Add E2E tests for category endpoints (Critical)
- [ ] Resolve PostingType vs CategoryType redundancy (Architectural)
- [ ] Add `GET /categories/{category_id}` endpoint (High)
- [ ] Implement CategoryInUseError validation (High)
- [ ] Remove commented imports (Medium)
- [ ] Fix exception handling specificity (Medium)
- [ ] Fix Decimal style in schemas.py (Low)
- [ ] Strengthen CategoryResponse.category_type typing (Low)

---

## Files Changed

| File | Change Type | Status |
|------|-------------|--------|
| `domain/model.py` | Modified | OK |
| `domain/exceptions.py` | Modified | OK |
| `service_layer/services.py` | Modified | Needs validation logic |
| `service_layer/abstract_repository.py` | Modified | OK |
| `adapters/orm.py` | Modified | OK |
| `adapters/repository.py` | Modified | OK |
| `api/schemas.py` | Modified | Minor fixes needed |
| `api/routers/categories.py` | **New** | Missing GET endpoint |
| `main.py` | Modified | OK |
| `tests/conftest.py` | Modified | **BROKEN** - parameter names |
| `tests/unit/*` | Modified | OK, but missing category tests |
| `tests/e2e/*` | Modified | OK, but missing category tests |
