# Service Layer Test Refactoring: Decoupling from Domain

This document outlines the proposal to transition service layer tests from "Low Gear" to "High Gear," as described in *Architecture Patterns with Python* (Chapter 5: TDD in High Gear and Low Gear).

## The Problem: Tight Coupling

Currently, the tests in `backend/tests/unit/test_services.py` are tightly coupled to the domain entities in `backend/app/domain/model.py`.

### Symptoms of Coupling
1.  **Manual Instantiation**: Tests manually create `Account`, `Posting`, and `Transfer` objects to populate the `FakeRepository`.
2.  **Property Assertions**: Tests assert on the internal attributes of domain objects returned by service functions.
3.  **Import Bloat**: `test_services.py` must import most of the domain model, making it sensitive to any changes in the domain layer.

If the internal structure of a domain entity changes (e.g., renaming an attribute or changing a constructor signature), both domain tests and service tests will fail, doubling the maintenance burden.

## The Goal: "High Gear" Service Tests

Refactor service tests to treat the service layer as a black box that accepts and returns primitives or simple data structures.

### Key Principles
1.  **Setup via Services**: Use service functions (e.g., `create_account`) to set up the system state instead of manually injecting objects into the repository.
2.  **Input/Output Primitives**: Pass strings, integers, and Decimals to service functions.
3.  **State Verification**: Verify outcomes by calling other service functions (e.g., `get_account`) or by checking the state of the repository using primitive identifiers.
4.  **Decoupled Assertions**: Assert on primitive values rather than domain object instances.

## Comparison

### Before (Low Gear / Coupled)
```python
def test_update_account_name_success():
    # Coupled to Account constructor
    account = Account(account_id="acc-1", name="Old Name", currency="USD", initial_balance=Decimal(100))
    repo = FakeRepository(accounts=[account])
    
    # Act
    updated_account = update_account_name(repo, account_id="acc-1", new_name="New Name")
    
    # Coupled to Account object properties
    assert updated_account.name == "New Name"
```

### After (High Gear / Decoupled)
```python
def test_update_account_name_success():
    repo = FakeRepository()
    # Setup using service
    account = create_account(repo, name="Old Name", currency="USD", initial_balance=Decimal(100))
    
    # Act
    update_account_name(repo, account_id=account.account_id, new_name="New Name")
    
    # Verify using another service
    updated_account = get_account(repo, account_id=account.account_id)
    assert updated_account.name == "New Name"
```

## Benefits
*   **Refactoring Safety**: Domain models can be refactored internally without breaking service-level regression tests.
*   **Documentation**: Service tests act as documentation for how the API/UI will interact with the system.
*   **Reduced Friction**: Adding new features to the domain doesn't require updating dozens of setup blocks in service tests.

## Implementation Plan
1.  Update `FakeRepository` if necessary to better support ID generation if not already handled.
2.  Refactor `TestCreateAccount` to verify state via `get_account` rather than the returned object's internal state.
3.  Refactor `TestUpdateAccountName`, `TestDeleteAccount`, and `TestCreatePosting` to use `create_account` for setup.
4.  Remove domain entity imports from `test_services.py` where possible.
