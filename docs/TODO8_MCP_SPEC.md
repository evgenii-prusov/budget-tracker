# TODO 8: MCP Server with Streamable HTTP Transport — Implementation Spec

## Context

This is the final task for the budget-tracker project. The product manifesto defines MCP as the **primary interface** — a hosted MCP server allowing Claude/ChatGPT mobile apps to act as personal financial assistants via 4 tools: `add_expense`, `transfer_funds`, `get_spending`, `list_accounts`.

All dependencies (TODOs 1-7) are complete. The MCP server will be mounted on the existing FastAPI app, reuse existing service layer functions, and authenticate with the same `API_KEY` Bearer token.

**Note:** The manifesto says "SSE transport" but SSE is deprecated in the FastMCP SDK. The modern equivalent is **Streamable HTTP** via `mcp.http_app()`, which provides the same persistent-connection capabilities that mobile LLM apps need. The spec uses `http_app()`.

## 1. New Dependencies

Add to `backend/pyproject.toml`:
```toml
dependencies = [
    ...existing...,
    "fastmcp>=2.0.0",
]
```

Then run `uv sync` from `backend/`.

The `fastmcp` package (PyPI: `fastmcp`) is the official high-level MCP SDK. It brings `starlette`, `sse-starlette`, `pydantic`, `httpx`, `uvicorn`. Requires Python 3.10+ (project uses 3.12+).

## 2. File Structure

```
backend/
  app/
    mcp/
      __init__.py          # Empty package init
      server.py            # FastMCP instance, tool definitions, lifespan, create_mcp_app()
      resolvers.py         # Name-to-ID resolution helpers
  tests/
    unit/
      test_mcp_tools.py    # Unit tests with FakeUnitOfWork
    e2e/
      test_mcp_api.py      # E2E tests via MCP Client + real DB
```

## 3. Authentication

Use a custom `TokenVerifier` subclass that reads the API key lazily at verification time via `get_api_key()`:

```python
from fastmcp.server.auth import AccessToken, TokenVerifier
from app.core.config import get_api_key

class _BearerTokenVerifier(TokenVerifier):
    """Validates a static Bearer API key. Reads API_KEY lazily at verification time."""

    async def verify_token(self, token: str) -> AccessToken | None:
        api_key = get_api_key()
        if token == api_key:
            return AccessToken(
                token=token,
                client_id="budget-tracker-user",
                scopes=["all"],
            )
        return None

def _build_auth() -> _BearerTokenVerifier:
    return _BearerTokenVerifier()
```

This validates `Authorization: Bearer <API_KEY>` on all MCP HTTP endpoints automatically.

## 4. Database / UoW Wiring

Use FastMCP's **lifespan** + **`Context`** pattern to inject UoW into tools:

```python
from contextlib import asynccontextmanager, contextmanager
from fastmcp.server.lifespan import lifespan
from app.core.db import Database
from app.adapters.unit_of_work import SqlAlchemyUnitOfWork

@lifespan
async def mcp_lifespan(server):
    db = Database()
    db.init()
    try:
        yield {"db": db}
    finally:
        db.dispose()

@contextmanager
def _uow_from_ctx(ctx):
    db = ctx.lifespan_context["db"]
    session = db.get_session()
    try:
        yield SqlAlchemyUnitOfWork(session)
    finally:
        session.close()
```

## 5. Name-to-ID Resolvers (`app/mcp/resolvers.py`)

LLM assistants use human-friendly names (e.g., "Cash EUR", "Groceries"), not UUIDs. Resolvers bridge this gap. Error messages list available options so the LLM can suggest corrections.

```python
def resolve_account_by_name(uow, name) -> Account
def resolve_account_by_currency(uow, currency) -> Account
def resolve_subcategory_by_name(uow, name) -> Category
```

## 6. MCP Tool Definitions (`app/mcp/server.py`)

### 6.1 `add_expense`
Record an expense. Finds account by currency (prefers non-savings). Subcategory must be an existing expense subcategory name.

### 6.2 `transfer_funds`
Transfer money between accounts. Use account names. Amounts can differ for cross-currency transfers.

### 6.3 `get_spending`
Get spending aggregated by parent category. Period: 'week', 'month', or 'year'.

### 6.4 `list_accounts`
List all accounts with balances. Use filter='savings' to show only savings accounts.

## 7. FastAPI Mounting (`app/main.py`)

```python
from app.mcp.server import create_mcp_app

mcp_app = create_mcp_app()
app.mount("/mcp", mcp_app)
```

## 8. Test Strategy (Strict TDD)

### 8.1 Unit Tests (`tests/unit/test_mcp_tools.py`)
- Extract core logic into `_*_impl()` functions that accept a UoW parameter
- Unit tests call `_*_impl(fake_uow, ...)` directly
- Test resolvers, tool implementations, error handling

### 8.2 E2E Tests (`tests/e2e/test_mcp_api.py`)
- Auth: verify 401 without token
- Tool listing: verify all 4 tools advertised
- Round-trip tests for key tools

## 9. TDD Implementation Order

1. Add `fastmcp` dependency → `uv sync`
2. Write resolver tests → run, verify they FAIL
3. Implement resolvers → run, verify they PASS
4. Write tool impl tests → run, verify they FAIL
5. Implement tool handlers → run, verify they PASS
6. Write e2e tests → run, verify they FAIL
7. Mount MCP on FastAPI → run, verify they PASS
8. Full verification: `make test && make typecheck && make quality`

## 10. Key Existing Code to Reuse

| What | Where |
|------|-------|
| `create_posting()` | `backend/app/service_layer/services.py:125` |
| `create_transfer()` | `backend/app/service_layer/services.py:309` |
| `get_spending_report()` | `backend/app/service_layer/reports.py:42` |
| `list_accounts()` | `backend/app/service_layer/services.py:37` |
| `get_api_key()` | `backend/app/core/config.py` |
| `Database` | `backend/app/core/db.py` |
| `SqlAlchemyUnitOfWork` | `backend/app/adapters/unit_of_work.py` |
| `FakeUnitOfWork` | `backend/tests/unit/test_services.py` |
| `PostingType`, `CategoryType` | `backend/app/domain/model.py` |
| Domain exceptions | `backend/app/domain/exceptions.py` |
| `TEST_API_KEY`, `JAN_01` etc. | `backend/tests/constants.py` |

## 11. Files to Modify

- `backend/pyproject.toml` — add `fastmcp>=2.0.0`
- `backend/app/main.py` — mount MCP app
- `backend/app/mcp/__init__.py` — NEW (empty)
- `backend/app/mcp/server.py` — NEW (FastMCP instance, tools, lifespan, factory)
- `backend/app/mcp/resolvers.py` — NEW (name-to-ID resolution)
- `backend/tests/unit/test_mcp_tools.py` — NEW (unit tests)
- `backend/tests/e2e/test_mcp_api.py` — NEW (e2e tests)
- `docs/TODO.md` — mark TODO 8 as done

## 12. Verification

1. `cd backend && uv run pytest tests/unit/test_mcp_tools.py -v` — all unit tests pass
2. `cd backend && uv run pytest tests/e2e/test_mcp_api.py -v` — all e2e tests pass
3. `cd backend && make test` — full test suite passes (no regressions)
4. `cd backend && make typecheck` — no type errors
5. `cd backend && make quality` — linting passes
