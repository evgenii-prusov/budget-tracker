# TODO 9: Per-Branch Review Fixes

Code review findings for the three implementation branches. Each section lists fixes scoped to that branch, to be addressed before merge.

---

## Branch: `feature/task-9.1-create-account-mcp` (TODO 9.1)

Commit reviewed: `66de8c2 fix: pre-commit check (type safety in tests)`

### 9.1-R1: Update module docstring `[Trivial]`

**File**: `backend/app/mcp/server.py:3`

The docstring says "Exposes 4 tools" — update to 5.

```python
# Before
"""MCP Server for budget-tracker.

Exposes 4 tools: add_expense, transfer_funds, get_spending, list_accounts.
...
"""

# After
"""MCP Server for budget-tracker.

Exposes 5 tools: create_account, add_expense, transfer_funds, get_spending, list_accounts.
...
"""
```

### 9.1-R2: Add E2E test for savings account and duplicate error `[Low]`

**File**: `backend/tests/e2e/test_mcp_api.py`

The current `test_create_account_roundtrip` only tests a basic non-savings account. Add assertions for:
1. Create a savings account (`is_savings: true`) and verify `[savings]` appears in `list_accounts` output
2. Attempt to create a duplicate name and verify a friendly error (not a 500)

---

## Branch: `task-9.2-create-category-mcp` (TODO 9.2)

Commit reviewed: `21bfcbe Implement create_category MCP tool (Task 9.2)`

### 9.2-R1: Update module docstring `[Trivial]`

Same as 9.1-R1 — update "Exposes 4 tools" to 5 with `create_category` in the list.

### 9.2-R2: Add E2E test using created category in `add_expense` `[Low]`

**File**: `backend/tests/e2e/test_mcp_api.py`

The spec says the E2E test should "create hierarchy then use in `add_expense`". The current test verifies categories via REST only. Extend `test_create_category_roundtrip` (or add a new test) that:
1. Creates parent + subcategory via MCP `create_category`
2. Creates an account via REST
3. Calls `add_expense` using the MCP-created subcategory
4. Asserts the expense was recorded successfully

This proves the full MCP-only workflow for category creation + expense recording.

---

## Branch: `feature/task-9.3-9.4-mcp-gaps` (TODO 9.3 + 9.4)

Commit reviewed: `e75f3da Add add_income MCP tool and account_name targeting`

### 9.3-R1: Add unit test for "neither currency nor account_name" error `[Medium]`

**File**: `backend/tests/unit/test_mcp_tools.py`

`_add_posting_impl` returns `"Either account_name or currency must be provided."` when both are `None`, but no test covers this path. Add to both `TestAddExpenseImpl` and `TestAddIncomeImpl`:

```python
def test_no_account_identifier_error(self):
    uow = self._setup_income_uow()  # or _setup_expense_uow()
    result = _add_income_impl(  # or _add_expense_impl
        uow,
        amount=Decimal("100"),
        subcategory="Salary",
        posting_date=JAN_01,
    )
    assert "account_name or currency must be provided" in result.lower()
```

Note: `_setup_expense_uow` is a module-level function, not a method — adjust the test for `TestAddExpenseImpl` accordingly.

### 9.3-R2: Improve docstrings for account identification `[Low]`

**File**: `backend/app/mcp/server.py`

Both `add_expense` and `add_income` tool wrappers should make it explicit that at least one account identifier is needed. MCP schema can't enforce "oneOf", so the docstring is the LLM's only guide.

```python
# In both add_expense and add_income docstrings, add:
"""...
Note: At least one of currency or account_name must be provided.
If both are given, account_name takes priority.
"""
```

### 9.3-R3: Add E2E test for `add_income` with `account_name` `[Low]`

**File**: `backend/tests/e2e/test_mcp_api.py`

There's `test_add_expense_with_account_name` but no equivalent for income. Add:

```python
@pytest.mark.asyncio
async def test_add_income_with_account_name(mcp_client, client):
    """Target a specific account by name for income."""
    _create_account(client, "Main EUR", "EUR", "1000.00")
    _create_account(client, "Side EUR", "EUR", "500.00")
    _create_category_hierarchy(client, "Income", "Freelance", "INCOME")

    result = await mcp_client.call_tool(
        "add_income",
        {
            "amount": "200.00",
            "account_name": "Side EUR",
            "subcategory": "Freelance",
            "posting_date": "2025-01-15",
        },
    )
    text = result.content[0].text
    assert "Side EUR" in text
    assert "700.0" in text  # 500 + 200
```

### 9.3-R4: Update module docstring `[Trivial]`

Same as 9.1-R1 — update "Exposes 4 tools" to 5 with `add_income` in the list.
