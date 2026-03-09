"""E2E tests for the MCP server.

Uses FastMCP in-memory Client for tool round-trips (real DB via test session),
and raw HTTP requests for auth verification.
"""

from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from fastmcp import Client, FastMCP

from app.mcp.server import _BearerTokenVerifier, _register_tools


@pytest.fixture
def mock_db(session):
    """A mock Database whose get_session() returns the test Postgres session."""
    db = MagicMock()
    db.get_session.return_value = session
    return db


@pytest.fixture
def mcp_server(mock_db):
    """A FastMCP instance wired to the test database."""

    @asynccontextmanager
    async def test_lifespan(server):
        yield {"db": mock_db}

    mcp = FastMCP(
        "Budget Tracker Test",
        auth=_BearerTokenVerifier(),
        lifespan=test_lifespan,
    )
    _register_tools(mcp)
    return mcp


@pytest_asyncio.fixture
async def mcp_client(mcp_server):
    """In-memory MCP client connected to the test server."""
    async with Client(mcp_server) as c:
        yield c


# ── Setup helpers (create data via REST API) ──────────────────────────


def _create_account(client, name, currency="EUR", initial_balance="1000.00", is_savings=False):
    resp = client.post(
        "/accounts/",
        json={
            "name": name,
            "currency": currency,
            "initial_balance": initial_balance,
            "is_savings": is_savings,
        },
    )
    assert resp.status_code == 201
    return resp.json()["account_id"]


def _create_category_hierarchy(client, parent_name, sub_name, category_type="EXPENSE"):
    parent_resp = client.post(
        "/categories/",
        json={"name": parent_name, "category_type": category_type},
    )
    assert parent_resp.status_code == 201
    parent_id = parent_resp.json()["category_id"]

    sub_resp = client.post(
        "/categories/",
        json={"name": sub_name, "category_type": category_type, "parent_id": parent_id},
    )
    assert sub_resp.status_code == 201
    return parent_id, sub_resp.json()["category_id"]


# ── Tests ─────────────────────────────────────────────────────────────


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


@pytest.mark.asyncio
async def test_create_account_roundtrip(mcp_client):
    """Create account via MCP tool then verify it via list_accounts tool."""
    await mcp_client.call_tool(
        "create_account",
        {
            "name": "MCP New Account",
            "currency": "USD",
            "initial_balance": "123.45",
            "is_savings": True,
        },
    )

    result = await mcp_client.call_tool("list_accounts", {"filter": "savings"})
    text = result.content[0].text
    assert "MCP New Account" in text
    assert "123.45" in text
    assert "USD" in text


@pytest.mark.asyncio
async def test_create_account_duplicate_error(mcp_client):
    """Duplicate account name returns a friendly error, not a 500."""
    await mcp_client.call_tool(
        "create_account",
        {"name": "Duplicate", "currency": "EUR"},
    )
    result = await mcp_client.call_tool(
        "create_account",
        {"name": "Duplicate", "currency": "USD"},
    )
    text = result.content[0].text
    assert "already exists" in text.lower()


@pytest.mark.asyncio
async def test_create_category_roundtrip(mcp_client, client):
    """Create parent then subcategory via MCP, verify via REST API."""
    # 1. Create parent category via MCP
    result = await mcp_client.call_tool(
        "create_category", {"name": "Travel", "category_type": "expense"}
    )
    text = result.content[0].text
    assert "Created EXPENSE parent category 'Travel'" in text

    # 2. Create subcategory via MCP
    result = await mcp_client.call_tool(
        "create_category",
        {"name": "Flights", "category_type": "expense", "parent_name": "Travel"},
    )
    text = result.content[0].text
    assert "Created EXPENSE subcategory 'Flights' under 'Travel'" in text

    # 3. Verify via REST API
    resp = client.get("/categories/")
    assert resp.status_code == 200
    categories = resp.json()

    # Find "Flights" subcategory
    flights = next((c for c in categories if c["name"] == "Flights"), None)
    assert flights is not None
    assert flights["category_type"] == "EXPENSE"
    assert flights["parent_id"] is not None

    # Find its parent
    parent = next((c for c in categories if c["category_id"] == flights["parent_id"]), None)
    assert parent is not None
    assert parent["name"] == "Travel"


@pytest.mark.asyncio
async def test_create_category_then_add_expense(mcp_client, client):
    """Create category hierarchy via MCP, then use it in add_expense."""
    _create_account(client, "Expense Acc", "EUR", "1000.00")

    # 1. Create parent + subcategory via MCP
    await mcp_client.call_tool(
        "create_category", {"name": "Shopping", "category_type": "expense"}
    )
    await mcp_client.call_tool(
        "create_category",
        {"name": "Clothes", "category_type": "expense", "parent_name": "Shopping"},
    )

    # 2. Record expense using the MCP-created subcategory
    result = await mcp_client.call_tool(
        "add_expense",
        {
            "amount": "75.00",
            "currency": "EUR",
            "subcategory": "Clothes",
            "posting_date": "2025-01-15",
        },
    )
    text = result.content[0].text
    assert "75.00" in text
    assert "Expense Acc" in text
    assert "Clothes" in text


@pytest.mark.asyncio
async def test_list_accounts_roundtrip(mcp_client, client):
    """Create accounts via REST API then list via MCP tool."""
    _create_account(client, "MCP Cash EUR", "EUR", "500.00")
    _create_account(client, "MCP Savings EUR", "EUR", "3000.00", is_savings=True)

    result = await mcp_client.call_tool("list_accounts", {})
    text = result.content[0].text
    assert "MCP Cash EUR" in text
    assert "MCP Savings EUR" in text


@pytest.mark.asyncio
async def test_list_accounts_savings_filter(mcp_client, client):
    """Savings filter should only return savings accounts."""
    _create_account(client, "MCP Regular", "EUR", "500.00")
    _create_account(client, "MCP Savings", "EUR", "3000.00", is_savings=True)

    result = await mcp_client.call_tool("list_accounts", {"filter": "savings"})
    text = result.content[0].text
    assert "MCP Savings" in text
    assert "MCP Regular" not in text


@pytest.mark.asyncio
async def test_add_expense_roundtrip(mcp_client, client):
    """Create account + category via REST, record expense via MCP."""
    _create_account(client, "Expense Account", "EUR", "1000.00")
    _create_category_hierarchy(client, "Food", "Groceries", "EXPENSE")

    result = await mcp_client.call_tool(
        "add_expense",
        {
            "amount": "42.50",
            "currency": "EUR",
            "subcategory": "Groceries",
            "posting_date": "2025-01-15",
        },
    )
    text = result.content[0].text
    assert "42.50" in text
    assert "Expense Account" in text


@pytest.mark.asyncio
async def test_add_expense_with_account_name(mcp_client, client):
    """Target a specific account by name instead of currency."""
    _create_account(client, "Main EUR", "EUR", "1000.00")
    _create_account(client, "Secondary EUR", "EUR", "200.00")
    _create_category_hierarchy(client, "Food", "Groceries", "EXPENSE")

    result = await mcp_client.call_tool(
        "add_expense",
        {
            "amount": "50.00",
            "account_name": "Secondary EUR",
            "subcategory": "Groceries",
            "posting_date": "2025-01-15",
        },
    )
    text = result.content[0].text
    assert "Secondary EUR" in text
    assert "150.0" in text  # 200 - 50


@pytest.mark.asyncio
async def test_add_income_roundtrip(mcp_client, client):
    """Create account + category via REST, record income via MCP."""
    _create_account(client, "Income Account", "EUR", "1000.00")
    _create_category_hierarchy(client, "Salary", "Bonus", "INCOME")

    result = await mcp_client.call_tool(
        "add_income",
        {
            "amount": "500.00",
            "currency": "EUR",
            "subcategory": "Bonus",
            "posting_date": "2025-01-15",
        },
    )
    text = result.content[0].text
    assert "500.00" in text
    assert "Income Account" in text
    assert "income" in text.lower()
    assert "1500.0" in text


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


@pytest.mark.asyncio
async def test_transfer_funds_roundtrip(mcp_client, client):
    """Create two accounts via REST, transfer via MCP."""
    _create_account(client, "Source ACC", "EUR", "1000.00")
    _create_account(client, "Dest ACC", "EUR", "200.00")

    result = await mcp_client.call_tool(
        "transfer_funds",
        {
            "from_account": "Source ACC",
            "to_account": "Dest ACC",
            "amount": "150.00",
            "transfer_date": "2025-01-15",
        },
    )
    text = result.content[0].text
    assert "150" in text
    assert "Source ACC" in text


@pytest.mark.asyncio
async def test_get_spending_report_roundtrip(mcp_client):
    """Get spending report (may be empty but should not error)."""
    result = await mcp_client.call_tool("get_spending", {"period": "month"})
    text = result.content[0].text
    assert "month" in text.lower() or "spending" in text.lower() or "No spending" in text


@pytest.mark.asyncio
async def test_add_expense_insufficient_funds(mcp_client, client):
    """Recording an expense beyond balance returns friendly error."""
    _create_account(client, "Small Account", "EUR", "10.00")
    _create_category_hierarchy(client, "Transport", "Taxi", "EXPENSE")

    result = await mcp_client.call_tool(
        "add_expense",
        {
            "amount": "999.99",
            "currency": "EUR",
            "subcategory": "Taxi",
            "posting_date": "2025-01-15",
        },
    )
    text = result.content[0].text
    assert "insufficient" in text.lower() or "Insufficient" in text


# ── Auth tests (HTTP-level) ──────────────────────────────────────────


def test_mcp_endpoint_rejects_no_auth(client_no_auth):
    """MCP endpoint returns 401 without Authorization header."""
    response = client_no_auth.get("/mcp/mcp")
    assert response.status_code == 401


def test_mcp_endpoint_rejects_invalid_token(client_no_auth):
    """MCP endpoint returns 401 with wrong Bearer token."""
    response = client_no_auth.get(
        "/mcp/mcp",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401
