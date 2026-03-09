# TODO 9: Integration Pass

After all three branches (9.1, 9.2, 9.3/9.4) have their review fixes applied and are individually merged, perform this integration pass to resolve cross-branch conflicts and finalize.

## Prerequisites

All three branches merged into `feature/mcp-server` (or `master`):
- `feature/task-9.1-create-account-mcp`
- `task-9.2-create-category-mcp`
- `feature/task-9.3-9.4-mcp-gaps`

---

## INT-1: Resolve merge conflicts in `test_list_tools` `[Required]`

**File**: `backend/tests/e2e/test_mcp_api.py`

All three branches independently rename `test_list_tools_returns_four` → `test_list_tools_returns_five` with different tool sets. After merging all three, the test should be:

```python
@pytest.mark.asyncio
async def test_list_tools_returns_seven(mcp_client):
    """The MCP server advertises exactly 7 tools."""
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert tool_names == {
        "create_account",
        "create_category",
        "add_expense",
        "add_income",
        "transfer_funds",
        "get_spending",
        "list_accounts",
    }
```

## INT-2: Resolve merge conflicts in `server.py` imports `[Required]`

**File**: `backend/app/mcp/server.py`

Each branch adds different imports. Combine them:

```python
from app.domain.exceptions import (
    CategoryHierarchyError,
    CategoryNotFoundError,
    DuplicateAccountNameError,
    DuplicateCategoryNameError,
    InsufficientFundsError,
    InvalidCurrencyError,
    InvalidInitialBalanceError,
)
from app.mcp.resolvers import (
    resolve_account_by_currency,
    resolve_account_by_name,
    resolve_parent_category_by_name,
    resolve_subcategory_by_name,
)
```

## INT-3: Resolve merge conflicts in `server.py` tool registration `[Required]`

**File**: `backend/app/mcp/server.py`, `_register_tools()`

All three branches insert new tools at the same point (before `add_expense`). After merge, the registration order should be:

1. `create_account` (from 9.1)
2. `create_category` (from 9.2)
3. `add_expense` (existing, modified by 9.3/9.4)
4. `add_income` (from 9.3)
5. `transfer_funds` (existing)
6. `get_spending` (existing)
7. `list_accounts` (existing)

This order mirrors the natural workflow: create accounts → create categories → record postings → transfer → review.

## INT-4: Resolve merge conflicts in unit test imports `[Required]`

**File**: `backend/tests/unit/test_mcp_tools.py`

Combine imports from all branches:

```python
from app.mcp.resolvers import (
    resolve_account_by_currency,
    resolve_account_by_name,
    resolve_parent_category_by_name,
    resolve_subcategory_by_name,
)
from app.mcp.server import (
    _add_expense_impl,
    _add_income_impl,
    _create_account_impl,
    _create_category_impl,
    _get_spending_report_impl,
    _list_accounts_impl,
    _transfer_funds_impl,
)
```

## INT-5: Update module docstring `[Low]`

**File**: `backend/app/mcp/server.py:1-5`

```python
"""MCP Server for budget-tracker.

Exposes 7 tools: create_account, create_category, add_expense, add_income,
transfer_funds, get_spending, list_accounts.
Uses FastMCP with Streamable HTTP transport, mounted on the FastAPI app at /mcp.
"""
```

## INT-6: Run full test suite `[Required]`

After resolving all conflicts:

```bash
cd backend && uv run pytest -v && make typecheck && make quality
```

## Merge Strategy Recommendation

To minimize conflict pain:
1. Merge **9.3/9.4** first (largest change — refactors `_add_expense_impl`)
2. Merge **9.1** second (independent — adds `create_account`)
3. Merge **9.2** last (adds resolver + `create_category`)

Rationale: 9.3/9.4 modifies `_add_expense_impl` which the other two branches don't touch. Merging it first avoids rebasing the refactored code. Branches 9.1 and 9.2 add code at the same insertion points but don't modify existing functions, so their conflicts will be purely additive.
