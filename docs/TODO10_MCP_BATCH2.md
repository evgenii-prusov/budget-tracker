# TODO 10: MCP Batch 2 — List Tools & Instructions Update

## Context

The MCP server currently exposes 7 tools covering account/category creation, posting recording, transfers, spending reports, and account listing. The remaining gaps prevent AI assistants from **discovering categories** and **reviewing transaction/transfer history** — essential for a complete UAT workflow.

This TODO covers 4 new MCP tools + an instructions update + test coverage for everything.

**Current tools**: `create_account`, `create_category`, `add_expense`, `add_income`, `transfer_funds`, `get_spending`, `list_accounts`

**Target**: 10 tools after this batch.

---

## TODO 10.1: `list_categories` MCP tool

**Why**: Without this, the AI must guess subcategory names when recording expenses/income. If it guesses wrong, it relies on error messages to discover valid names — a poor UX.

**Service layer** (already exists):
- `services.list_categories(uow)` → all categories
- `services.list_parent_categories(uow)` → parent categories only
- `services.list_subcategories(uow, parent_id=...)` → children of a parent

**Implementation plan**:

1. Add `_list_categories_impl(uow, *, category_type: str | None = None) -> str` to `server.py`
   - Call `services.list_parent_categories(uow)` to get all parents
   - For each parent, call `services.list_subcategories(uow, parent_id=...)` to get children
   - If `category_type` is provided (`"expense"` or `"income"`), filter parents by type
   - Format as a hierarchical tree:
     ```
     Expense categories:
       • Food
         - Groceries
         - Restaurants
       • Transport
         - Uber

     Income categories:
       • Employment
         - Salary
     ```
   - Return `"No categories found."` if empty

2. Add `@mcp.tool() list_categories(category_type, ctx)` wrapper in `_register_tools()`
   - `category_type: str | None = None` — optional filter: `"expense"`, `"income"`, or omit for all
   - Validate `category_type` string → `CategoryType` enum (same pattern as `create_category`)

**Files to modify**:
- `backend/app/mcp/server.py` — add `_list_categories_impl()` + tool wrapper

**Tests (TDD — write first)**:

Unit tests in `test_mcp_tools.py`:
- `test_list_categories_empty` — no categories → `"No categories found."`
- `test_list_categories_with_hierarchy` — parents + subcategories → correct tree format
- `test_list_categories_filter_expense` — only expense categories shown
- `test_list_categories_filter_income` — only income categories shown
- `test_list_categories_invalid_type` — invalid type string → friendly error

E2E test in `test_mcp_api.py`:
- `test_list_categories_roundtrip` — create categories via MCP, list via MCP, verify output

---

## TODO 10.2: `list_postings` MCP tool

**Why**: Enables reviewing recorded expenses and income — completing UAT step 5 ("review transaction history"). Without this, the AI records transactions but can never verify or summarize them.

**Service layer** (already exists):
- `services.list_postings(uow, account_id=None, skip=0, limit=50)` → list of `Posting` objects
- Each `Posting` has: `posting_id`, `account_id`, `amount`, `posting_date`, `category_id`, `posting_type`, `payee`, `description`

**Implementation plan**:

1. Add `_list_postings_impl(uow, *, account_name: str | None = None, limit: int = 20) -> str` to `server.py`
   - If `account_name` provided, resolve via `resolve_account_by_name(uow, account_name)` to get `account_id`
   - Call `services.list_postings(uow, account_id=..., limit=limit)`
   - To show category and account names in output, need to look up:
     - Account name: `uow.accounts.get(posting.account_id).name` and `.currency`
     - Category name: `uow.categories.get(posting.category_id).name`
   - Format each posting as a line:
     ```
     2025-01-15  EXPENSE  42.50 EUR  [Groceries]  Payee: Lidl  (Cash EUR)
     ```
   - Return `"No postings found."` if empty
   - Default limit of 20 to avoid overwhelming LLM context

2. Add `@mcp.tool() list_postings(account_name, limit, ctx)` wrapper in `_register_tools()`
   - `account_name: str | None = None` — optional filter by account
   - `limit: str = "20"` — max number of postings (parsed to int)

**Files to modify**:
- `backend/app/mcp/server.py` — add `_list_postings_impl()` + tool wrapper

**Tests (TDD — write first)**:

Unit tests in `test_mcp_tools.py`:
- `test_list_postings_empty` — no postings → `"No postings found."`
- `test_list_postings_with_data` — postings present → formatted output with date, type, amount, category, payee
- `test_list_postings_account_filter` — only postings from specified account
- `test_list_postings_unknown_account` — friendly error for nonexistent account name

E2E test in `test_mcp_api.py`:
- `test_list_postings_roundtrip` — add expense via MCP, then list postings and verify it appears

---

## TODO 10.3: `list_transfers` MCP tool

**Why**: Enables reviewing fund transfers between accounts — the other half of UAT step 5. Without this, the AI can't verify whether transfers were recorded correctly.

**Service layer** (already exists):
- `services.list_transfers(uow, skip=0, limit=50)` → list of `Transfer` objects
- Each `Transfer` has: `transfer_id`, `source_account_id`, `dest_account_id`, `debit_amount`, `credit_amount`, `transfer_date`, `description`

**Implementation plan**:

1. Add `_list_transfers_impl(uow, *, limit: int = 20) -> str` to `server.py`
   - Call `services.list_transfers(uow, limit=limit)`
   - For each transfer, look up account names:
     - `uow.accounts.get(transfer.source_account_id)` → name + currency
     - `uow.accounts.get(transfer.dest_account_id)` → name + currency
   - Format each transfer:
     - Same currency: `2025-01-15  Cash EUR → Savings EUR  200.00 EUR`
     - Cross-currency: `2025-01-15  Cash EUR → Cash USD  100.00 EUR → 110.00 USD`
   - Include description if present
   - Return `"No transfers found."` if empty

2. Add `@mcp.tool() list_transfers(limit, ctx)` wrapper in `_register_tools()`
   - `limit: str = "20"` — max number of transfers (parsed to int)

**Files to modify**:
- `backend/app/mcp/server.py` — add `_list_transfers_impl()` + tool wrapper

**Tests (TDD — write first)**:

Unit tests in `test_mcp_tools.py`:
- `test_list_transfers_empty` — no transfers → `"No transfers found."`
- `test_list_transfers_same_currency` — formatted output with account names
- `test_list_transfers_cross_currency` — shows both amounts with currencies
- `test_list_transfers_with_description` — description included in output

E2E test in `test_mcp_api.py`:
- `test_list_transfers_roundtrip` — transfer via MCP, then list and verify

---

## TODO 10.4: Update MCP `instructions` and tool count

**Why**: The `instructions` string in `_create_mcp()` tells AI assistants what the server can do. After adding 3 new tools, it must be updated so assistants discover and use them. The E2E test `test_list_tools_returns_seven` must also be updated.

**Implementation plan**:

1. Rewrite the `instructions` string in `_create_mcp()`:
   - List all 10 tools grouped by purpose
   - Include brief workflow guidance: create accounts → create categories → record postings → review (list categories, list postings, list transfers, get spending)

2. Update `server.py` module docstring to list all 10 tools

3. Update E2E test `test_list_tools_returns_seven` → `test_list_tools_returns_ten`:
   - Add `list_categories`, `list_postings`, `list_transfers` to expected set

**Files to modify**:
- `backend/app/mcp/server.py` — `_create_mcp()` instructions, module docstring
- `backend/tests/e2e/test_mcp_api.py` — tool count test

---

## Execution Order

```
10.1 list_categories ─┐
10.2 list_postings ────┼── can be done in any order (independent)
10.3 list_transfers ───┘
         │
         ▼
10.4 instructions + tool count ── after all tools added
```

Each TODO follows TDD: write failing tests → implement → verify green.

## Verification

After all TODOs:
```bash
cd backend && uv run pytest -v && make typecheck && make quality
```

## Key Files Reference

| File | Role |
|------|------|
| `backend/app/mcp/server.py` | All MCP tools, `_impl` functions, tool registration |
| `backend/app/mcp/resolvers.py` | Name-to-ID resolution helpers |
| `backend/app/service_layer/services.py` | `list_categories`, `list_postings`, `list_transfers` (no changes needed) |
| `backend/app/domain/model.py` | `Posting`, `Transfer`, `Account`, `Category` models |
| `backend/tests/unit/test_mcp_tools.py` | Unit tests for `_impl` functions |
| `backend/tests/e2e/test_mcp_api.py` | E2E tests with FastMCP Client |
