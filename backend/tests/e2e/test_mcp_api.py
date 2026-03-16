"""E2E tests for the MCP server.

Uses FastMCP in-memory Client for tool round-trips (real DB via test session),
and raw HTTP requests for auth verification.
"""

from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from fastmcp import Client, FastMCP

from app.mcp.server import _register_tools


@pytest.fixture
def mock_db(session):
    """A mock Database whose get_session() returns the test Postgres session."""
    db = MagicMock()
    db.get_session.return_value = session
    return db


@pytest.fixture
def mcp_server(mock_db):
    """A FastMCP instance wired to the test database.

    Uses no auth for in-memory Client testing (auth is tested separately
    in test_mcp_oauth.py via HTTP).
    """

    @asynccontextmanager
    async def test_lifespan(server):
        yield {"db": mock_db}

    mcp = FastMCP(
        "Budget Tracker Test",
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
async def test_list_tools_returns_sixteen(mcp_client):
    """The MCP server advertises exactly 16 tools."""
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
        "list_categories",
        "list_postings",
        "list_transfers",
        "delete_posting",
        "delete_transfer",
        "delete_account",
        "delete_category",
        "update_account",
        "update_category",
    }


@pytest.mark.asyncio
async def test_list_postings_roundtrip(mcp_client, client):
    """Create account + category via REST, record expense via MCP, then list via MCP."""
    _create_account(client, "Postings Acc", "EUR", "1000.00")
    _create_category_hierarchy(client, "Food", "Restaurants", "EXPENSE")

    # 1. Add expense via MCP
    await mcp_client.call_tool(
        "add_expense",
        {
            "amount": "15.50",
            "account_name": "Postings Acc",
            "subcategory": "Restaurants",
            "posting_date": "2025-01-20",
            "payee": "Salad Bar",
        },
    )

    # 2. List postings via MCP
    result = await mcp_client.call_tool("list_postings", {"account_name": "Postings Acc"})
    text = result.content[0].text
    assert "2025-01-20" in text
    assert "15.50" in text
    assert "Restaurants" in text
    assert "Salad Bar" in text
    assert "Postings Acc" in text


@pytest.mark.asyncio
async def test_list_categories_roundtrip(mcp_client, client):
    """Create categories via MCP, list via MCP, verify output."""
    # 1. Create hierarchy via MCP
    await mcp_client.call_tool("create_category", {"name": "Health", "category_type": "expense"})
    await mcp_client.call_tool(
        "create_category",
        {"name": "Dentist", "category_type": "expense", "parent_name": "Health"},
    )
    await mcp_client.call_tool("create_category", {"name": "Gift", "category_type": "income"})

    # 2. List categories via MCP
    result = await mcp_client.call_tool("list_categories", {})
    text = result.content[0].text

    assert "Expense categories:" in text
    assert "• Health" in text
    assert "  - Dentist" in text
    assert "Income categories:" in text
    assert "• Gift" in text

    # 3. Test filtering
    result_exp = await mcp_client.call_tool("list_categories", {"category_type": "expense"})
    text_exp = result_exp.content[0].text
    assert "Expense categories:" in text_exp
    assert "Income categories:" not in text_exp


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
    # Different currency but same name should still fail
    result = await mcp_client.call_tool(
        "create_account",
        {"name": "Duplicate", "currency": "USD"},
    )
    text = result.content[0].text
    assert "already exists" in text.lower()


@pytest.mark.asyncio
async def test_update_account(mcp_client):
    """Test updating account name and description via MCP tool."""
    await mcp_client.call_tool(
        "create_account",
        {
            "name": "To Be Updated",
            "currency": "EUR",
            "description": "Old description",
        },
    )

    # Update both name and description
    result = await mcp_client.call_tool(
        "update_account",
        {
            "account_name": "To Be Updated",
            "new_name": "Updated Name",
            "description": "New description",
            "update_description": True,
        },
    )
    assert "Updated account 'To Be Updated'" in result.content[0].text

    # Verify the update via list_accounts
    list_result = await mcp_client.call_tool("list_accounts", {})
    text = list_result.content[0].text
    assert "Updated Name" in text
    assert "New description" in text
    assert "To Be Updated" not in text

    # Try to update non-existent account
    result_not_found = await mcp_client.call_tool(
        "update_account",
        {"account_name": "Non Existent", "new_name": "New Name"},
    )
    assert "No account named" in result_not_found.content[0].text


@pytest.mark.asyncio
async def test_update_account_clear_description(mcp_client):
    """Test clearing an account's description via update_description=True."""
    await mcp_client.call_tool(
        "create_account",
        {
            "name": "Clear Desc",
            "currency": "USD",
            "description": "Has description",
        },
    )

    # Clear description
    result = await mcp_client.call_tool(
        "update_account",
        {
            "account_name": "Clear Desc",
            "description": None,
            "update_description": True,
        },
    )
    assert "description to null" in result.content[0].text

    # Verify via list_accounts
    list_result = await mcp_client.call_tool("list_accounts", {})
    text = list_result.content[0].text
    # We check that the specific line for this account doesn't show the description
    # list_accounts formats description as " (Old description)" or similar.
    # In server.py: lines.append(f"  • {acc.name}: {acc.balance} {acc.currency}{desc_str}")
    # where desc_str = f" ({acc.description})" if acc.description else ""
    assert "Clear Desc:" in text
    assert "(Has description)" not in text


@pytest.mark.asyncio
async def test_update_account_no_op(mcp_client):
    """Test calling update_account with no changes provided."""
    await mcp_client.call_tool(
        "create_account",
        {"name": "No Op", "currency": "EUR"},
    )

    result = await mcp_client.call_tool(
        "update_account",
        {"account_name": "No Op"},
    )
    assert "No updates provided" in result.content[0].text


@pytest.mark.asyncio
async def test_update_account_initial_balance(mcp_client):
    """Test updating an account's initial_balance via MCP tool."""
    await mcp_client.call_tool(
        "create_account",
        {"name": "Balance Update", "currency": "EUR", "initial_balance": "100"},
    )

    result = await mcp_client.call_tool(
        "update_account",
        {
            "account_name": "Balance Update",
            "initial_balance": 250.50,
            "update_initial_balance": True,
        },
    )
    assert "initial_balance to 250.5" in result.content[0].text

    # Verify via list_accounts
    list_result = await mcp_client.call_tool("list_accounts", {})
    text = list_result.content[0].text
    assert "250.5" in text


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
async def test_update_category(mcp_client):
    """Test updating category name via MCP tool."""
    # 1. Create a parent category
    await mcp_client.call_tool(
        "create_category", {"name": "Old Parent", "category_type": "expense"}
    )

    # 2. Update it
    result = await mcp_client.call_tool(
        "update_category",
        {"name": "Old Parent", "category_type": "expense", "new_name": "New Parent"},
    )
    assert "Updated expense category 'Old Parent' name to 'New Parent'" in result.content[0].text

    # 3. Verify via list_categories
    list_result = await mcp_client.call_tool("list_categories", {"category_type": "expense"})
    text = list_result.content[0].text
    assert "New Parent" in text
    assert "Old Parent" not in text

    # 4. Create and update a subcategory
    await mcp_client.call_tool(
        "create_category", {"name": "Sub", "category_type": "expense", "parent_name": "New Parent"}
    )
    result_sub = await mcp_client.call_tool(
        "update_category",
        {"name": "New Parent/Sub", "category_type": "expense", "new_name": "New Sub"},
    )
    text_sub_update = result_sub.content[0].text
    assert "Updated expense category 'New Parent/Sub' name to 'New Sub'" in text_sub_update

    # 5. Verify subcategory update
    list_result_sub = await mcp_client.call_tool("list_categories", {"category_type": "expense"})
    text_sub = list_result_sub.content[0].text
    assert "New Parent" in text_sub
    assert "New Sub" in text_sub
    # Check that 'Sub' is not present as a standalone word/name in the lines
    sub_lines = [line.strip() for line in text_sub.split("\n") if line.strip().startswith("-")]
    assert "- Sub" not in sub_lines


@pytest.mark.asyncio
async def test_create_category_with_description(mcp_client, client):
    """Create a category with description via MCP, verify in output and REST API."""
    result = await mcp_client.call_tool(
        "create_category",
        {"name": "Housing", "category_type": "expense", "description": "Rent and utilities"},
    )
    text = result.content[0].text
    assert "Created EXPENSE parent category 'Housing'" in text

    # Verify description via REST API
    resp = client.get("/categories/")
    categories = resp.json()
    housing = next((c for c in categories if c["name"] == "Housing"), None)
    assert housing is not None
    assert housing["description"] == "Rent and utilities"


@pytest.mark.asyncio
async def test_list_categories_shows_description(mcp_client):
    """Categories with descriptions show them in list output."""
    await mcp_client.call_tool(
        "create_category",
        {"name": "Food", "category_type": "expense", "description": "All food expenses"},
    )
    await mcp_client.call_tool(
        "create_category",
        {
            "name": "Drinks",
            "category_type": "expense",
            "parent_name": "Food",
            "description": "Beverages only",
        },
    )

    result = await mcp_client.call_tool("list_categories", {"category_type": "expense"})
    text = result.content[0].text
    assert "All food expenses" in text
    assert "Beverages only" in text


@pytest.mark.asyncio
async def test_update_category_description(mcp_client):
    """Update a category's description via MCP tool."""
    await mcp_client.call_tool("create_category", {"name": "Transport", "category_type": "expense"})

    result = await mcp_client.call_tool(
        "update_category",
        {
            "name": "Transport",
            "category_type": "expense",
            "description": "Public and private transport",
            "update_description": True,
        },
    )
    text = result.content[0].text
    assert "Updated" in text
    assert "Transport" in text

    # Verify via list
    list_result = await mcp_client.call_tool("list_categories", {"category_type": "expense"})
    assert "Public and private transport" in list_result.content[0].text


@pytest.mark.asyncio
async def test_create_category_then_add_expense(mcp_client, client):
    """Create category hierarchy via MCP, then use it in add_expense."""
    _create_account(client, "Expense Acc", "EUR", "1000.00")

    # 1. Create parent + subcategory via MCP
    await mcp_client.call_tool("create_category", {"name": "Shopping", "category_type": "expense"})
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
async def test_list_transfers_roundtrip(mcp_client, client):
    """Transfer funds via MCP, then list transfers to verify."""
    _create_account(client, "Source ACC", "EUR", "1000.00")
    _create_account(client, "Dest ACC", "EUR", "200.00")

    await mcp_client.call_tool(
        "transfer_funds",
        {
            "from_account": "Source ACC",
            "to_account": "Dest ACC",
            "amount": "150.00",
            "transfer_date": "2025-01-15",
            "description": "Roundtrip test",
        },
    )

    result = await mcp_client.call_tool("list_transfers", {"limit": "10"})
    text = result.content[0].text
    assert "2025-01-15" in text
    assert "Source ACC → Dest ACC" in text
    assert "150.0" in text
    assert "Roundtrip test" in text


@pytest.mark.asyncio
async def test_list_transfers_invalid_limit(mcp_client):
    """Providing an invalid limit to list_transfers returns a friendly error."""
    # 1. Non-integer
    result = await mcp_client.call_tool("list_transfers", {"limit": "abc"})
    assert "Invalid limit" in result.content[0].text

    # 2. Out of range (low)
    result = await mcp_client.call_tool("list_transfers", {"limit": "0"})
    assert "Must be between 1 and 100" in result.content[0].text

    # 3. Out of range (high)
    result = await mcp_client.call_tool("list_transfers", {"limit": "101"})
    assert "Must be between 1 and 100" in result.content[0].text


@pytest.mark.asyncio
async def test_list_postings_invalid_limit(mcp_client):
    """Providing an invalid limit to list_postings returns a friendly error."""
    result = await mcp_client.call_tool("list_postings", {"limit": "-1"})
    assert "Must be between 1 and 100" in result.content[0].text


@pytest.mark.asyncio
async def test_get_spending_report_roundtrip(mcp_client):
    """Get spending report (may be empty but should not error)."""
    result = await mcp_client.call_tool("get_spending", {"period": "month"})
    text = result.content[0].text
    assert "month" in text.lower() or "spending" in text.lower() or "No spending" in text


@pytest.mark.asyncio
async def test_get_spending_report_with_reference_date(mcp_client):
    """Get spending report with a reference_date anchors the period to that month."""
    result = await mcp_client.call_tool(
        "get_spending", {"period": "month", "reference_date": "2025-01-15"}
    )
    text = result.content[0].text
    # The report always embeds start/end dates for January 2025.
    assert "2025-01-01" in text


@pytest.mark.asyncio
async def test_get_spending_report_invalid_reference_date(mcp_client):
    """Invalid reference_date returns a friendly error message."""
    result = await mcp_client.call_tool(
        "get_spending", {"period": "month", "reference_date": "not-a-date"}
    )
    text = result.content[0].text
    assert "Invalid" in text or "invalid" in text.lower()


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


# ── Deletion tool tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_posting_roundtrip(mcp_client, client):
    """Create account + expense via REST, delete posting via MCP."""
    account_id = _create_account(client, "Cash EUR", "EUR", "1000.00")

    # Add expense via REST
    posting_resp = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "42.50",
            "posting_date": "2025-01-15",
            "posting_type": "EXPENSE",
        },
    )
    assert posting_resp.status_code == 201
    posting_id = posting_resp.json()["posting_id"]

    result = await mcp_client.call_tool("delete_posting", {"posting_id": posting_id})
    text = result.content[0].text
    assert posting_id in text

    # Verify deleted via REST
    assert client.get(f"/postings/{posting_id}").status_code == 404


@pytest.mark.asyncio
async def test_delete_posting_not_found(mcp_client):
    """Deleting a nonexistent posting returns a friendly error."""
    result = await mcp_client.call_tool("delete_posting", {"posting_id": "nonexistent-id"})
    text = result.content[0].text
    assert "nonexistent-id" in text
    assert "not found" in text.lower()


@pytest.mark.asyncio
async def test_delete_transfer_roundtrip(mcp_client, client):
    """Create accounts + transfer via REST, delete transfer via MCP."""
    src_id = _create_account(client, "Source EUR", "EUR", "1000.00")
    dst_id = _create_account(client, "Dest EUR", "EUR", "500.00")

    transfer_resp = client.post(
        "/transfers/",
        json={
            "source_account_id": src_id,
            "dest_account_id": dst_id,
            "debit_amount": "100.00",
            "credit_amount": "100.00",
            "transfer_date": "2025-01-15",
        },
    )
    assert transfer_resp.status_code == 201
    transfer_id = transfer_resp.json()["transfer_id"]

    result = await mcp_client.call_tool("delete_transfer", {"transfer_id": transfer_id})
    text = result.content[0].text
    assert transfer_id in text

    # Verify deleted via REST
    assert client.get(f"/transfers/{transfer_id}").status_code == 404


@pytest.mark.asyncio
async def test_delete_transfer_not_found(mcp_client):
    """Deleting a nonexistent transfer returns a friendly error."""
    result = await mcp_client.call_tool("delete_transfer", {"transfer_id": "nonexistent-id"})
    text = result.content[0].text
    assert "nonexistent-id" in text
    assert "not found" in text.lower()


@pytest.mark.asyncio
async def test_delete_account_roundtrip(mcp_client, client):
    """Create account via REST (no postings/transfers), delete via MCP."""
    _create_account(client, "Empty Account", "EUR", "0.00")

    result = await mcp_client.call_tool("delete_account", {"account_name": "Empty Account"})
    text = result.content[0].text
    assert "Empty Account" in text

    # Verify deleted — account should no longer appear in list
    list_result = await mcp_client.call_tool("list_accounts", {})
    assert "Empty Account" not in list_result.content[0].text


@pytest.mark.asyncio
async def test_delete_account_not_found(mcp_client):
    """Deleting a nonexistent account returns a friendly error."""
    result = await mcp_client.call_tool("delete_account", {"account_name": "Ghost Account"})
    text = result.content[0].text
    assert "Ghost Account" in text
    assert "No account named" in text


@pytest.mark.asyncio
async def test_delete_category_roundtrip(mcp_client, client):
    """Create a parent category via REST, delete via MCP."""
    client.post("/categories/", json={"name": "Temp Category", "category_type": "EXPENSE"})

    result = await mcp_client.call_tool(
        "delete_category", {"name": "Temp Category", "category_type": "EXPENSE"}
    )
    text = result.content[0].text
    assert "Temp Category" in text


@pytest.mark.asyncio
async def test_delete_category_not_found(mcp_client):
    """Deleting a nonexistent category returns a friendly error."""
    result = await mcp_client.call_tool(
        "delete_category", {"name": "Ghost Category", "category_type": "EXPENSE"}
    )
    text = result.content[0].text
    assert "Ghost Category" in text
    assert "No parent category named" in text


# ── Auth tests (HTTP-level) ──────────────────────────────────────────


def test_mcp_endpoint_rejects_no_auth(client_no_auth):
    """MCP endpoint returns 401 without Authorization header."""
    response = client_no_auth.get("/mcp")
    assert response.status_code == 401


def test_mcp_endpoint_rejects_invalid_token(client_no_auth):
    """MCP endpoint returns 401 with wrong Bearer token."""
    response = client_no_auth.get(
        "/mcp",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401
