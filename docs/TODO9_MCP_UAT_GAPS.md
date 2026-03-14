# TODO 9: MCP UAT Readiness — Gap Analysis & Implementation Plan

## Context

The budget tracker REST API is fully functional with comprehensive CRUD operations. The MCP server (TODO 8) exposes 4 tools: `add_expense`, `transfer_funds`, `get_spending`, `list_accounts`. These are insufficient for User Acceptance Testing, where an external AI assistant (Claude.ai, Gemini, ChatGPT) connects via MCP to perform a realistic personal finance workflow:

1. Create accounts (checking, savings, credit cards, multiple currencies)
2. Create expense/income categories with subcategories
3. Add expenses and income for at least one week
4. Make transfers between accounts
5. Review spending reports and transaction history

**Current blocker**: Steps 1-3 cannot even begin — account creation, category creation, and income recording are all missing from MCP.

## Gap Summary

### Critical (Blocks workflow entirely)

| # | Gap | Why blocked | Service exists? |
|---|-----|-------------|-----------------|
| 9.1 | No `create_account` tool | Can't set up accounts — step 1 impossible | ✅ Completed |
| 9.2 | No `create_category` tool | Can't create categories — step 2 impossible, `add_expense` fails | ✅ Completed |
| 9.3 | No `add_income` tool | `add_expense` hardcodes `PostingType.EXPENSE` — income impossible | ✅ Completed |

### Important (Severely limits workflow)

| # | Gap | Why limited | Service exists? |
|---|-----|-------------|-----------------|
| 9.4 | `add_expense` can't target specific account | With 2+ EUR accounts, always picks first non-savings via `resolve_account_by_currency` | ✅ Completed |
| 9.5 | No `list_categories` tool | AI must guess subcategory names, relies on error messages for discovery | ✅ Completed |
| 9.6 | No `list_postings` tool | Can't review transaction history — step 5 incomplete | ✅ Completed |
| 9.7 | No `list_transfers` tool | Can't review transfer history — step 5 incomplete | ✅ Completed |

### Nice-to-have (Polish)

| # | Gap | Why |
|---|-----|-----|
| 9.8 | `get_spending` missing `reference_date` param | ✅ Completed |
| 9.9 | MCP `instructions` string outdated | ✅ Completed |
| 9.10 | MCP tools lack unit/e2e test coverage for new tools | ✅ Completed |

---

## Detailed TODOs

### TODO 9.1: `create_account` MCP tool `[S]`

**Description**: Expose account creation via MCP so the AI can set up checking, savings, and credit card accounts in any currency.

**Service**: `services.create_account(uow, *, name, currency, initial_balance, is_savings=False)`

**Implementation**:
- `_create_account_impl(uow, *, name, currency, initial_balance, is_savings)` → returns formatted confirmation string
- Tool wrapper parses `initial_balance` from string to `Decimal`, `is_savings` from string to bool
- Catch `DuplicateAccountNameError` → friendly error message

**Files**:
- `backend/app/mcp/server.py` — add `_create_account_impl()` + `@mcp.tool() create_account()`

**TDD**:
1. Unit test in `backend/tests/unit/test_mcp_tools.py`: success case, duplicate name error
2. E2E test in `backend/tests/e2e/test_mcp_api.py`: round-trip create + list

---

### TODO 9.2: `create_category` MCP tool `[S]`

**Description**: Expose category and subcategory creation. The AI needs to create parent categories (e.g., "Food", "Transport") and subcategories (e.g., "Groceries", "Uber") before recording expenses.

**Service**: `services.create_category(uow, *, name, category_type, parent_id=None)`

**Implementation**:
- `_create_category_impl(uow, *, name, category_type, parent_name=None)` → returns confirmation string
- `category_type` parameter: accepts `"expense"` or `"income"` string, maps to `CategoryType` enum
- If `parent_name` is provided, resolve it to a parent category ID (new resolver or inline lookup)
- Catch `DuplicateCategoryNameError`, `CategoryHierarchyError` → friendly error messages

**New resolver needed**: `resolve_parent_category_by_name(uow, name, category_type)` — finds top-level categories (where `parent_id is None`) by name. Add to `backend/app/mcp/resolvers.py`.

**Files**:
- `backend/app/mcp/resolvers.py` — add `resolve_parent_category_by_name()`
- `backend/app/mcp/server.py` — add `_create_category_impl()` + `@mcp.tool() create_category()`

**TDD**:
1. Unit test resolver: success, not found (lists available parents)
2. Unit test impl: create parent, create subcategory, duplicate name error
3. E2E test: create hierarchy then use in `add_expense`

---

### TODO 9.3: `add_income` MCP tool `[S]`

**Description**: Record income postings. Structurally identical to `add_expense` but uses `PostingType.INCOME` and resolves income subcategories (`CategoryType.INCOME`).

**Service**: `services.create_posting(uow, ..., posting_type=PostingType.INCOME)`

**Implementation**:
- `_add_income_impl(uow, *, amount, currency, subcategory, posting_date, payee=None, description=None)` → confirmation string
- Mirrors `_add_expense_impl` but resolves with `category_type=CategoryType.INCOME`
- Alternatively, refactor to share logic with `_add_expense_impl` via a private `_add_posting_impl` with a `posting_type` parameter — keeps code DRY

**Files**:
- `backend/app/mcp/server.py` — add `_add_income_impl()` (or `_add_posting_impl()`) + `@mcp.tool() add_income()`

**TDD**:
1. Unit test: record income, verify balance increases, verify income subcategory resolution
2. E2E test: create income category + subcategory, record income, verify via `list_accounts`

---

### TODO 9.4: `add_expense` account targeting `[S]`

**Description**: Add optional `account_name` parameter to `add_expense` (and `add_income`). When provided, resolve by name instead of currency. This is essential when the user has multiple accounts in the same currency (e.g., "Checking EUR" and "Business EUR").

**Implementation**:
- Add `account_name: str | None = None` parameter to `_add_expense_impl()` and the tool wrapper
- If `account_name` is provided: use `resolve_account_by_name(uow, account_name)`
- If not provided: fall back to existing `resolve_account_by_currency(uow, currency)` behavior
- Apply same change to `add_income` / `_add_income_impl()`

**Files**:
- `backend/app/mcp/server.py` — modify `_add_expense_impl()`, `add_expense()`, and new income tool

**TDD**:
1. Unit test: expense with `account_name` targets correct account, without falls back to currency

---

### TODO 9.5: `list_categories` MCP tool `[S]`

**Description**: List all categories, grouped by type (expense/income) and showing parent→subcategory hierarchy. Essential for the AI to discover available subcategories before recording postings.

**Service**: `services.list_categories(uow)`, `services.list_parent_categories(uow)`, `services.list_subcategories(uow, parent_id=...)`

**Implementation**:
- `_list_categories_impl(uow, *, category_type=None)` → formatted tree string
- Optional `category_type` filter: `"expense"`, `"income"`, or `None` for all
- Output format: hierarchical tree, e.g.:
  ```
  Expense categories:
    • Food
      - Groceries
      - Restaurants
    • Transport
      - Uber
  ```

**Files**:
- `backend/app/mcp/server.py` — add `_list_categories_impl()` + `@mcp.tool() list_categories()`

**TDD**:
1. Unit test: empty list, with categories, filter by type
2. E2E test: create categories via REST, verify via MCP tool

---

### TODO 9.6: `list_postings` MCP tool `[S]`

**Description**: List recent transactions (expenses and income) with optional account filter. Enables the AI to review what has been recorded.

**Service**: `services.list_postings(uow, *, account_id=None, skip=0, limit=50)`

**Implementation**:
- `_list_postings_impl(uow, *, account_name=None, limit=20)` → formatted list string
- If `account_name` provided, resolve to ID via `resolve_account_by_name()`
- Output format: date, type, amount, currency, subcategory, payee
- Default limit of 20 to avoid overwhelming LLM context

**Files**:
- `backend/app/mcp/server.py` — add `_list_postings_impl()` + `@mcp.tool() list_postings()`

**TDD**:
1. Unit test: empty list, with postings, account filter
2. E2E test: add expense via MCP, then list and verify it appears

---

### TODO 9.7: `list_transfers` MCP tool `[S]`

**Description**: List recent transfers between accounts.

**Service**: `services.list_transfers(uow, skip=0, limit=50)`

**Implementation**:
- `_list_transfers_impl(uow, *, limit=20)` → formatted list string
- Output: date, from→to, amount(s), description
- Cross-currency transfers show both amounts

**Files**:
- `backend/app/mcp/server.py` — add `_list_transfers_impl()` + `@mcp.tool() list_transfers()`

**TDD**:
1. Unit test: empty list, same-currency transfer, cross-currency transfer
2. E2E test: transfer via MCP, then list and verify

---

### TODO 9.8: `get_spending` add `reference_date` parameter `[S]`

**Description**: The `_get_spending_report_impl` function already accepts `reference_date` but the tool wrapper doesn't expose it. Add it so the AI can view past periods.

**Implementation**:
- Add `reference_date: str | None = None` to the `get_spending` tool wrapper
- Parse with `date.fromisoformat()`, pass to `_get_spending_report_impl`

**Files**:
- `backend/app/mcp/server.py` — modify `get_spending()` tool wrapper

**TDD**:
1. Unit test: report with specific reference_date
2. E2E test: add expenses, query past period

---

### TODO 9.9: Update MCP `instructions` string `[S]`

**Description**: The `instructions` parameter in `_create_mcp()` currently describes only 4 tools. Update it to reflect all available tools so AI assistants can discover and use them effectively.

**Implementation**:
- Rewrite the `instructions` string in `_create_mcp()` to list all tools and their purposes
- Include brief guidance on workflow order (create accounts → categories → record postings → review)

**Files**:
- `backend/app/mcp/server.py` — modify `_create_mcp()` instructions

---

### TODO 9.10: Unit & E2E tests for new MCP tools `[M]`

**Description**: Add comprehensive test coverage for all new tools, following existing patterns.

**Unit tests** (`backend/tests/unit/test_mcp_tools.py`):
- Follow existing pattern: test `_*_impl()` functions with `FakeUnitOfWork`
- Cover happy paths, error cases, edge cases (empty lists, duplicate names, etc.)

**E2E tests** (`backend/tests/e2e/test_mcp_api.py`):
- Follow existing pattern: FastMCP in-memory `Client` + real test Postgres DB
- Round-trip tests: create via MCP tool → verify via another MCP tool or REST
- Update tool listing test to verify new tool count

**Files**:
- `backend/tests/unit/test_mcp_tools.py`
- `backend/tests/e2e/test_mcp_api.py`

---

## Dependency Graph

```
9.1 create_account ──┐
                     ├──→ 9.4 account targeting (needs multiple accounts)
9.2 create_category ─┤
                     ├──→ 9.3 add_income (needs income categories)
                     │
                     ├──→ 9.5 list_categories (useful after creation)
                     │
                     └──→ 9.6 list_postings (needs postings to list)
                          9.7 list_transfers (needs transfers to list)

9.8 get_spending reference_date ── independent
9.9 instructions update ── after all tools added
9.10 tests ── parallel with each TODO (TDD: test first)
```

## Recommended Execution Order

**Batch 1 — Critical blockers (unblocks UAT steps 1-3):**
1. TODO 9.1: `create_account` — unblocks step 1
2. TODO 9.2: `create_category` — unblocks step 2
3. TODO 9.3: `add_income` — unblocks step 3

**Batch 2 — Important for usable workflow:**
4. TODO 9.4: `add_expense` account targeting
5. TODO 9.5: `list_categories`
6. TODO 9.6: `list_postings`
7. TODO 9.7: `list_transfers`

**Batch 3 — Polish:**
8. TODO 9.8: `get_spending` reference_date
9. TODO 9.9: Update instructions
10. TODO 9.10: Ensure full test coverage

**Note**: Each TODO follows TDD — write tests first as part of implementation, not deferred to the end. TODO 9.10 covers any remaining test gaps after individual TODOs.

## Verification

1. Cross-reference with UAT workflow steps 1-5 — all steps achievable after batch 2
2. Cross-reference with REST API endpoints — no CRUD operations missing from MCP
3. Review `backend/app/service_layer/services.py` — all needed services already exist
4. After implementation: `cd backend && uv run pytest -v && make typecheck && make quality`

## Key Files Reference

| File | Role |
|------|------|
| `backend/app/mcp/server.py` | All MCP tools, `_impl` functions, tool registration |
| `backend/app/mcp/resolvers.py` | Name-to-ID resolution helpers |
| `backend/app/service_layer/services.py` | All service functions (no changes needed) |
| `backend/app/service_layer/reports.py` | Spending report service |
| `backend/app/domain/model.py` | `PostingType`, `CategoryType` enums |
| `backend/app/domain/exceptions.py` | Domain exceptions for error handling |
| `backend/tests/unit/test_mcp_tools.py` | Unit test patterns for `_impl` functions |
| `backend/tests/e2e/test_mcp_api.py` | E2E test patterns with FastMCP Client |
