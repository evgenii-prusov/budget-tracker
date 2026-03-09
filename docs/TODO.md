# Budget Tracker: Implementation TODO List

Derived from the [Product Manifesto](./PRODUCT_MANIFESTO.md) gap analysis.

---

## Phase 1: Independent Domain Enhancements (no dependencies, any order)

### TODO 1: Add `is_savings` Flag to Account `[S]` (Completed)
Add boolean `is_savings` field (default `False`) to Account. Full vertical slice: domain model, ORM, migration, API schemas, service layer, tests.
- `backend/app/domain/model.py` — add `is_savings` param to `Account.__init__` [DONE]
- `backend/app/adapters/orm.py` — add `Boolean` column [DONE]
- `backend/app/api/schemas.py` — add to `AccountCreate`, `AccountResponse` [DONE]
- `backend/app/service_layer/services.py` — pass through `create_account` [DONE]
- New Alembic migration + tests at all levels [DONE]

### TODO 2: Add `payee` and `description` Fields to Posting `[S]` (Completed)
Add optional `payee: str | None` and `description: str | None` to Posting. Thread through `Account.record_posting()`, service layer, API schemas.
- `backend/app/domain/model.py` — add params to `Posting.__init__`, `Account.record_posting` [DONE]
- `backend/app/adapters/orm.py` — add columns to `posting` table [DONE]
- `backend/app/api/schemas.py` — add to `PostingCreate`, `PostingResponse` [DONE]
- `backend/app/service_layer/services.py` — pass through `create_posting` [DONE]
- New Alembic migration + tests at all levels [DONE]

### TODO 3: Expose Account Balance in API Response `[S]` (Completed)
`Account.balance` property exists but `AccountResponse` omits it. Add `balance`/`current_balance` to the response schema.
- `backend/app/api/schemas.py` — add `balance` to `AccountResponse` [DONE]
- `backend/app/api/routers/accounts.py` — adjust response construction if needed [DONE]
- e2e tests for accounts [DONE]

---

## Phase 2: Category Restructure

### TODO 4: 2-Level Category Hierarchy + Type Enforcement `[L]`
**Deps: None** (but benefits from TODOs 1-2 being done first to reduce test churn)

Add `parent_id` (nullable self-FK) and `category_type` (Income/Expense enum) to Category. Enforce: parents have `parent_id=null`, subcategories point to a parent, max 2 levels. Postings must reference subcategories only.
- `backend/app/domain/model.py` — add `parent_id`, `category_type`, validation
- `backend/app/adapters/orm.py` — self-referential FK, enum column
- `backend/app/service_layer/abstract_category_repository.py` — new queries (`list_children`, `get_with_children`)
- `backend/app/adapters/category_repository.py` — implement new queries
- `backend/app/service_layer/services.py` — enforce subcategory-only on posting creation
- `backend/app/api/schemas.py` — update `CategoryCreate`, `CategoryResponse`
- `backend/app/api/routers/categories.py` — endpoints for parent/child listing
- New Alembic migration + data migration strategy for existing categories
- Extensive tests at all levels

---

## Phase 3: Infrastructure + Reporting

### TODO 5: Authentication (Bearer Token) `[M]` (Completed)
**Deps: None**

Single-tenant shared-secret auth. `API_KEY` env var, FastAPI dependency checking `Authorization: Bearer <token>`.
- New: `backend/app/api/auth.py` — auth dependency [DONE]
- `backend/app/core/config.py` — `get_api_key()` config [DONE]
- `backend/app/main.py` — apply globally [DONE]
- All e2e tests + `conftest.py` — add auth header fixture [DONE]

### TODO 6: Spending Reports `[M]` (Completed)
**Deps: TODO 1 (`is_savings`), TODO 4 (parent categories)**

New read-only aggregation service: spending by period (week/month/year), grouped by parent category, filterable by savings accounts. SQL-based aggregation for efficiency.
- New: `backend/app/service_layer/reports.py`
- New: `backend/app/api/routers/reports.py` + response schemas
- `backend/app/main.py` — register router
- Tests at unit + e2e level

### TODO 7: Backend Dockerfile `[S]` (Completed)
**Deps: None**

Production Dockerfile for FastAPI backend. Add to `docker-compose.yml`. Health check, uvicorn CMD, env handling.
- New: `backend/Dockerfile`, `backend/.dockerignore` [DONE]
- `docker-compose.yml` — add backend service [DONE]

---

## Phase 4: MCP Server

### TODO 8: MCP Server with Streamable HTTP Transport `[L]` (Completed)
**Deps: TODO 1, TODO 2, TODO 4, TODO 5, TODO 6**

The primary interface per manifesto. MCP server exposing tools: `add_expense`, `transfer_funds`, `get_spending_report`, `list_accounts`. Streamable HTTP transport for mobile LLM app connections.
- `backend/pyproject.toml` — added `fastmcp>=2.0.0` dependency [DONE]
- New: `backend/app/mcp/__init__.py` — package init [DONE]
- New: `backend/app/mcp/resolvers.py` — name-to-ID resolution helpers [DONE]
- New: `backend/app/mcp/server.py` — FastMCP instance, tools, lifespan, auth [DONE]
- `backend/app/main.py` — mount MCP app at `/mcp` [DONE]
- New: `backend/tests/unit/test_mcp_tools.py` — unit tests (29 tests) [DONE]
- New: `backend/tests/e2e/test_mcp_api.py` — e2e tests (7 tests) [DONE]

---

## Dependency Graph
```
TODO 1 (is_savings) ──────────────┐
TODO 2 (payee/desc) ──────────────┤
TODO 3 (balance in API) [terminal]│
                                  │
TODO 4 (categories) ──────────────┼──→ TODO 6 (reports) ──→ TODO 8 (MCP)
                                  │                    ↗
TODO 5 (auth) ────────────────────┘───────────────────╯
TODO 7 (Dockerfile) [terminal]
```

## Recommended Execution Order
1. **Batch 1 (parallel-safe):** TODOs 1, 2, 3 — small, independent
2. **Batch 2:** TODO 4 — largest structural change
3. **Batch 3 (parallel-safe):** TODOs 5, 6, 7 — auth, reports, Docker
4. **Batch 4:** TODO 8 — MCP server (depends on most above)

## Verification (per TODO)
1. `make test` — all existing + new tests pass
2. `make typecheck` — no type errors
3. `make quality` — linting passes
4. Manual API testing via `make run` + curl/httpie for new endpoints