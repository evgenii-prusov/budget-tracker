# PR #88 Copilot Review — TODO List

12 comments from Copilot, grouped by theme.

---

## 1. Resolver type-safety: EXPENSE vs INCOME subcategories

**Problem:** `resolve_subcategory_by_name()` returns any subcategory regardless of `category_type`. If an INCOME subcategory shares a name with an EXPENSE one, `add_expense` will pass the wrong category to `create_posting`, causing a `CategoryHierarchyError` that isn't caught.

- [ ] **1a.** Add `category_type` filter to `resolve_subcategory_by_name()` (or create a dedicated `resolve_expense_subcategory()`) — `resolvers.py:46`
- [ ] **1b.** Add unit test: INCOME subcategory passed to `add_expense` returns friendly error — `test_mcp_tools.py`
- [ ] **1c.** Catch `CategoryHierarchyError` in `_add_expense_impl` alongside `InsufficientFundsError` — `server.py:88`

## 2. Missing error handling for domain exceptions

**Problem:** `_transfer_funds_impl` only catches `InsufficientFundsError`. The domain `Transfer` raises `ValueError` for non-positive amounts, which would crash the tool.

- [ ] **2a.** Catch `ValueError` in `_transfer_funds_impl` and return user-facing message — `server.py:126`
- [ ] **2b.** Add unit tests for zero/negative amounts in `transfer_funds` — `test_mcp_tools.py`

## 3. Context nullability

**Problem:** Tool functions declare `ctx: Context | None = None` but `_uow_from_ctx` requires a real `Context`. If FastMCP ever skips injection, this crashes at runtime.

- [ ] **3.** Either make `ctx` non-optional on tool signatures, or add a guard in `_uow_from_ctx` — `server.py:57`

## 4. Duplicate Database instance

**Problem:** MCP lifespan creates its own `Database()` while FastAPI already has `app.state.db`. This duplicates connection pools.

- [ ] **4.** Consider sharing the Database instance (e.g., pass it into `create_mcp_app()`) — `server.py:196`, `main.py`

## 5. Tool name inconsistency in docs

**Problem:** The implementation uses `get_spending` but 4 places in docs still say `get_spending_report`.

- [ ] **5a.** Fix module docstring — `server.py:4`
- [ ] **5b.** Fix spec section 6.3 — `docs/TODO8_MCP_SPEC.md:112`
- [ ] **5c.** Fix spec intro — `docs/TODO8_MCP_SPEC.md:6`
- [ ] **5d.** Fix TODO entry — `docs/TODO.md:86`

## 6. Spec doesn't match implementation (auth)

**Problem:** Spec describes `StaticTokenVerifier` but implementation uses custom `_BearerTokenVerifier` with lazy `get_api_key()`.

- [ ] **6.** Update spec auth section to reflect actual implementation — `docs/TODO8_MCP_SPEC.md:48`
