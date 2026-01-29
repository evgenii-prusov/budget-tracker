# Senior Backend Engineer Code Review

**Date**: 2026-01-28
**Reviewer Perspective**: Senior Backend Engineer (BigTech)
**Project**: Budget Tracker

---

## Executive Summary

This is **good code for a personal project or MVP**. The architecture demonstrates solid understanding of clean code principles. The testing strategy is above average.

For **production at scale**, several areas need hardening around transaction management, error handling, input validation, and observability.

---

## What You're Doing Well

### 1. Clean Architecture Implementation

Your separation of concerns is solid. Domain layer has zero framework dependencies, service layer orchestrates use cases, adapters handle persistence. This is textbook clean architecture and shows you understand the principles, not just cargo-culting patterns.

**Layer Structure**:
| Layer | Location | Dependencies |
|-------|----------|--------------|
| Domain | `app/domain/` | None |
| Service | `app/service_layer/` | Domain only |
| Adapters | `app/adapters/` | Domain, Service |
| API | `app/api/` | All layers |

### 2. Testing Strategy

The FakeRepository approach over mocks is exactly right. Your tests verify *behavior* not *implementation*. The test pyramid (unit → integration → e2e) is well-balanced. This is how production code should be tested.

```python
# Good: FakeRepository tests outcomes, not implementation
class FakeRepository(AbstractRepository):
    def __init__(self, accounts: list[Account] | None = None):
        self.accounts = accounts or []
        self.committed = False
```

### 3. Domain Modeling

- Decimal enforcement with runtime validation is correct for financial applications
- The sign convention in `Account.record_posting()` is smart encapsulation
- The `create_transfer` function with rollback logic shows thinking about invariants

### 4. Type Safety

- Good use of type hints throughout
- `PostingType` as `StrEnum` is clean
- Pydantic schemas handle API boundary validation well

---

## Areas That Need Attention

### 1. Transaction Management is Fragile ⚠️

**Location**: `backend/app/service_layer/services.py`

**Problem**:
```python
# services.py:42
account.name = new_name
repo.commit()  # What if this fails?
```

Every service function calls `commit()` individually. This creates several problems:
- No Unit of Work pattern — you can't batch operations
- Error handling is inconsistent (some places rollback, some don't)
- The domain `create_transfer` rollback (lines 311-313) is manual list manipulation — brittle

**Recommendation**: Introduce a proper Unit of Work that commits at the end of a request, not per-operation.

**Priority**: High

---

### 2. The `except Exception` Anti-pattern 🔴

**Location**: `backend/app/api/routers/accounts.py:47-49` (and other routers)

**Problem**:
```python
except Exception as exc:
    repo.rollback()
    raise HTTPException(status_code=400, detail=str(exc))
```

This catches *everything* — including programming errors, TypeErrors, etc. — and returns them as 400 Bad Request with the raw exception message. In production this:
- Leaks internal implementation details to clients
- Makes debugging harder (all errors look the same)
- Could expose sensitive information

**Recommendation**: Remove these catch-all blocks. Let unexpected exceptions bubble up as 500s with proper logging. Use FastAPI exception handlers for consistent error responses.

**Priority**: Critical

---

### 3. Currency Validation is Missing 🔴

**Location**: `backend/app/domain/model.py:180`

**Problem**:
```python
self.currency = currency  # Just accepts any string
```

CLAUDE.md mentions `VALID_CURRENCIES` but no validation exists. You can create an account with currency "BITCOIN" or "asdf".

**Recommendation**: Add ISO 4217 validation in the domain layer:
```python
VALID_CURRENCIES = {"USD", "EUR", "GBP", "RUB", ...}

def __init__(self, ..., currency: str, ...):
    if currency not in VALID_CURRENCIES:
        raise InvalidCurrencyError(f"Invalid currency: {currency}")
    self.currency = currency
```

**Priority**: High

---

### 4. The Dependency Module Does Too Much ⚠️

**Location**: `backend/app/api/dependencies.py:28-34`

**Problem**:
```python
_ensure_mappers_started()
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)  # DDL on import!
```

Database initialization happens at import time. This:
- Makes testing harder (you need to override globals)
- Prevents proper configuration management
- The `_ensure_mappers_started()` pattern with try/except is a code smell

**Recommendation**: Use factory functions or proper application lifecycle management (FastAPI lifespan events).

**Priority**: Medium

---

### 5. Missing Pagination ⚠️

**Location**: All `list_*` endpoints

**Problem**:
```python
def list_accounts(repo: RepoDep):
    return repo.list_all()  # What if there are 100,000 accounts?
```

All list endpoints return unbounded results.

**Recommendation**: Add pagination parameters:
```python
@router.get("/accounts")
def list_accounts(
    repo: RepoDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    return repo.list_all(skip=skip, limit=limit)
```

**Priority**: Medium (for personal finance app, Low initially)

---

### 6. No Logging

**Location**: Entire codebase

**Problem**: Zero logging statements. When something goes wrong in production, you'll be blind.

**Recommendation**: At minimum, log:
- Business operations (account created, transfer made)
- Errors and exceptions
- Request/response for debugging

```python
import logging
logger = logging.getLogger(__name__)

def create_account(repo, *, name, currency, initial_balance):
    logger.info(f"Creating account: {name}, {currency}")
    # ...
    logger.info(f"Account created: {new_account.account_id}")
```

**Priority**: High for production

---

### 7. Account Deletion is Asymmetric

**Location**: `backend/app/service_layer/services.py:76-90`

**Problem**: Transfers block account deletion, but postings cascade-delete silently. Is this intentional? Deleting an account removes all expense history without warning.

**Recommendation**: Either:
- Block deletion if postings exist (consistent with transfers)
- Add explicit confirmation/warning mechanism
- Document the intentional asymmetry

**Priority**: Medium (business logic decision)

---

### 8. The Balance Property is O(n) ⚠️

**Location**: `backend/app/domain/model.py:186-191`

**Problem**:
```python
@property
def balance(self) -> Decimal:
    posting_sum = sum(p.amount for p in self._postings)
    outgoing_sum = sum(t.debit_amount for t in self._outgoing_transfers)
    incoming_sum = sum(t.credit_amount for t in self._incoming_transfers)
    return self.initial_balance + posting_sum - outgoing_sum + incoming_sum
```

Every balance access iterates all postings and transfers. With thousands of transactions, this becomes slow.

**Recommendation**: Consider:
- Caching the computed balance
- A database computed column
- Incremental updates on posting/transfer creation

**Priority**: Low (optimize when needed)

---

## Minor Observations

| Issue | Location | Notes |
|-------|----------|-------|
| ID generation | `model.py` | `str(uuid4())` is fine, but consider `uuid7` for sortable IDs |
| No API versioning | `main.py` | No `/v1/` prefix makes breaking changes harder |
| CORS hardcoded | `main.py` | `localhost:5173` needs configuration for deployment |
| Python version constraint | `pyproject.toml` | `>=3.12,<3.14` upper bound will break when 3.14 releases |

---

## Action Items Summary

### Critical (Fix Before Production)
- [x] Remove `except Exception` catch-all blocks
- [x] Add currency validation

### High Priority
- [x] Implement proper transaction management / Unit of Work
- [ ] Add logging infrastructure

### Medium Priority
- [ ] Refactor dependency injection / app lifecycle
- [ ] Add pagination to list endpoints
- [ ] Clarify account deletion policy

### Low Priority / Tech Debt
- [ ] Optimize balance calculation
- [ ] Add API versioning
- [ ] Make CORS configurable
- [ ] Consider UUID7 for IDs

---

## Conclusion

The bones are solid. The issues are typical of early-stage projects that prioritized getting functionality working over production hardening. That's often the right trade-off — just be aware of the debt.

The architecture allows these improvements to be made incrementally without major rewrites, which is a sign of good foundational design.
