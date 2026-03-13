"""MCP Server for budget-tracker.

Exposes 11 tools: create_account, create_category, add_expense, add_income,
transfer_funds, get_spending, list_accounts, list_categories, list_postings,
list_transfers, delete_posting.
Uses FastMCP with Streamable HTTP transport, mounted on the FastAPI app at /mcp.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from fastmcp import Context, FastMCP
from fastmcp.server.auth import AccessToken, TokenVerifier

from app.adapters.unit_of_work import SqlAlchemyUnitOfWork
from app.core.config import get_api_key
from app.core.db import Database
from app.domain.exceptions import (
    CategoryHierarchyError,
    CategoryNotFoundError,
    DuplicateAccountNameError,
    DuplicateCategoryNameError,
    InsufficientFundsError,
    InvalidCurrencyError,
    InvalidInitialBalanceError,
    PostingNotFoundError,
)
from app.domain.model import CategoryType, PostingType
from app.mcp.resolvers import (
    resolve_account_by_currency,
    resolve_account_by_name,
    resolve_parent_category_by_name,
    resolve_subcategory_by_name,
)
from app.service_layer import services
from app.service_layer.reports import get_spending_report

if TYPE_CHECKING:
    from app.service_layer.unit_of_work import AbstractUnitOfWork


# ── Auth ──────────────────────────────────────────────────────────────


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


# ── UoW helper ────────────────────────────────────────────────────────


@contextmanager
def _uow_from_ctx(ctx: Context):
    db: Database = ctx.lifespan_context["db"]
    session = db.get_session()
    try:
        uow = SqlAlchemyUnitOfWork(session)
        yield uow
    finally:
        session.close()


# ── Tool implementations (pure logic, testable with FakeUnitOfWork) ──


def _create_account_impl(
    uow: AbstractUnitOfWork,
    *,
    name: str,
    currency: str,
    initial_balance: Decimal,
    is_savings: bool = False,
) -> str:
    try:
        account = services.create_account(
            uow,
            name=name,
            currency=currency,
            initial_balance=initial_balance,
            is_savings=is_savings,
        )
    except (DuplicateAccountNameError, InvalidInitialBalanceError, InvalidCurrencyError) as exc:
        return str(exc)

    tag = " (savings)" if account.is_savings else ""
    return (
        f"Created account '{account.name}'{tag} "
        f"with initial balance {account.initial_balance} {account.currency}."
    )


def _create_category_impl(
    uow: AbstractUnitOfWork,
    *,
    name: str,
    category_type_str: str,
    parent_name: str | None = None,
) -> str:
    # 1. Map category_type string to enum
    try:
        category_type = CategoryType(category_type_str.upper())
    except ValueError:
        return f"Invalid category type: '{category_type_str}'. Use 'expense' or 'income'."

    # 2. Resolve parent if name provided
    parent_id = None
    if parent_name:
        try:
            parent = resolve_parent_category_by_name(uow, parent_name, category_type=category_type)
            parent_id = parent.category_id
        except ValueError as exc:
            return str(exc)

    # 3. Create the category
    try:
        services.create_category(
            uow,
            name=name,
            category_type=category_type,
            parent_id=parent_id,
        )
    except (DuplicateCategoryNameError, CategoryHierarchyError, CategoryNotFoundError) as exc:
        return str(exc)

    kind = "subcategory" if parent_id else "parent category"
    msg = f"Created {category_type.value} {kind} '{name}'"
    if parent_id is not None:
        msg += f" under '{parent.name}'"
    msg += "."
    return msg


def _add_posting_impl(
    uow: AbstractUnitOfWork,
    *,
    amount: Decimal,
    posting_type: PostingType,
    category_type: CategoryType,
    currency: str | None = None,
    account_name: str | None = None,
    subcategory: str,
    posting_date: date,
    payee: str | None = None,
    description: str | None = None,
) -> str:
    try:
        if account_name:
            account = resolve_account_by_name(uow, account_name)
        elif currency:
            account = resolve_account_by_currency(uow, currency)
        else:
            return "Either account_name or currency must be provided."

        category = resolve_subcategory_by_name(uow, subcategory, category_type=category_type)
    except ValueError as exc:
        return str(exc)

    try:
        posting = services.create_posting(
            uow,
            account_id=account.account_id,
            amount=amount,
            posting_date=posting_date,
            posting_type=posting_type,
            category_id=category.category_id,
            payee=payee,
            description=description,
        )
    except (InsufficientFundsError, CategoryHierarchyError) as exc:
        return str(exc)

    verb = "expense" if posting_type == PostingType.EXPENSE else "income"
    return (
        f"Recorded {verb} of {abs(posting.amount)} {account.currency} "
        f"on {account.name} under {subcategory}."
        + (f" Payee: {payee}." if payee else "")
        + f" New balance: {account.balance} {account.currency}."
    )


def _add_expense_impl(
    uow: AbstractUnitOfWork,
    *,
    amount: Decimal,
    currency: str | None = None,
    account_name: str | None = None,
    subcategory: str,
    posting_date: date,
    payee: str | None = None,
    description: str | None = None,
) -> str:
    return _add_posting_impl(
        uow,
        amount=amount,
        posting_type=PostingType.EXPENSE,
        category_type=CategoryType.EXPENSE,
        currency=currency,
        account_name=account_name,
        subcategory=subcategory,
        posting_date=posting_date,
        payee=payee,
        description=description,
    )


def _add_income_impl(
    uow: AbstractUnitOfWork,
    *,
    amount: Decimal,
    currency: str | None = None,
    account_name: str | None = None,
    subcategory: str,
    posting_date: date,
    payee: str | None = None,
    description: str | None = None,
) -> str:
    return _add_posting_impl(
        uow,
        amount=amount,
        posting_type=PostingType.INCOME,
        category_type=CategoryType.INCOME,
        currency=currency,
        account_name=account_name,
        subcategory=subcategory,
        posting_date=posting_date,
        payee=payee,
        description=description,
    )


def _transfer_funds_impl(
    uow: AbstractUnitOfWork,
    *,
    from_account: str,
    to_account: str,
    amount: Decimal,
    to_amount: Decimal | None = None,
    transfer_date: date,
    description: str | None = None,
) -> str:
    try:
        source = resolve_account_by_name(uow, from_account)
        dest = resolve_account_by_name(uow, to_account)
    except ValueError as exc:
        return str(exc)

    credit = to_amount if to_amount is not None else amount
    try:
        services.create_transfer(
            uow,
            source_account_id=source.account_id,
            dest_account_id=dest.account_id,
            debit_amount=amount,
            credit_amount=credit,
            transfer_date=transfer_date,
            description=description,
        )
    except (InsufficientFundsError, ValueError) as exc:
        return str(exc)

    msg = f"Transferred {amount} {source.currency} from {source.name}"
    if credit != amount:
        msg += f" → {credit} {dest.currency} to {dest.name}."
    else:
        msg += f" to {dest.name}."
    msg += f" Source balance: {source.balance} {source.currency}."
    return msg


def _get_spending_report_impl(
    uow: AbstractUnitOfWork,
    *,
    period: str,
    reference_date: date | None = None,
) -> str:
    try:
        report = get_spending_report(uow, period=period, reference_date=reference_date)
    except ValueError as exc:
        return str(exc)

    if not report.rows:
        return f"No spending found for {report.period} ({report.start_date} to {report.end_date})."

    lines = [f"Spending report ({report.period}: {report.start_date} to {report.end_date}):"]
    for row in report.rows:
        lines.append(f"  • {row.parent_category_name}: {row.total} {row.currency}")
    return "\n".join(lines)


def _list_accounts_impl(
    uow: AbstractUnitOfWork,
    filter: str | None = None,
) -> str:
    accounts = services.list_accounts(uow, skip=0, limit=200)

    if filter == "savings":
        accounts = [a for a in accounts if a.is_savings]

    if not accounts:
        return "No accounts found."

    lines = []
    for acc in accounts:
        tag = " [savings]" if acc.is_savings else ""
        lines.append(f"• {acc.name}: {acc.balance} {acc.currency}{tag}")
    return "\n".join(lines)


def _list_categories_impl(
    uow: AbstractUnitOfWork,
    *,
    category_type_str: str | None = None,
) -> str:
    # 1. Map category_type string to enum if provided
    category_type = None
    if category_type_str:
        try:
            category_type = CategoryType(category_type_str.upper())
        except ValueError:
            return f"Invalid category type: '{category_type_str}'. Use 'expense' or 'income'."

    # 2. Get all parent categories, filtered by type if requested
    # Fetch categories with a generous limit to ensure all are shown in typical use cases
    parents = services.list_parent_categories(uow, limit=500)
    if category_type:
        parents = [p for p in parents if p.category_type == category_type]

    if not parents:
        return "No categories found."

    # 3. Format as a hierarchical tree
    expense_parents = [p for p in parents if p.category_type == CategoryType.EXPENSE]
    income_parents = [p for p in parents if p.category_type == CategoryType.INCOME]

    lines = []
    if expense_parents:
        lines.append("Expense categories:")
        for p in expense_parents:
            lines.append(f"  • {p.name}")
            # Use pre-loaded p.children instead of redundant service calls
            subs = sorted(p.children, key=lambda c: c.name)
            for s in subs:
                lines.append(f"    - {s.name}")

    if income_parents:
        if lines:
            lines.append("")
        lines.append("Income categories:")
        for p in income_parents:
            lines.append(f"  • {p.name}")
            # Use pre-loaded p.children instead of redundant service calls
            subs = sorted(p.children, key=lambda c: c.name)
            for s in subs:
                lines.append(f"    - {s.name}")

    return "\n".join(lines)


def _list_postings_impl(
    uow: AbstractUnitOfWork,
    *,
    account_name: str | None = None,
    limit: int = 20,
) -> str:
    account_id = None
    if account_name:
        try:
            account = resolve_account_by_name(uow, account_name)
            account_id = account.account_id
        except ValueError as exc:
            return str(exc)

    postings = services.list_postings(uow, account_id=account_id, limit=limit)

    if not postings:
        return "No postings found."

    # Sort postings by date (newest first)
    postings.sort(key=lambda p: p.posting_date, reverse=True)

    # Bulk load accounts and categories to avoid N+1 queries
    account_ids = {p.account_id for p in postings}
    category_ids = {p.category_id for p in postings if p.category_id}

    accounts_map = {}
    for acc_id in account_ids:
        acc = uow.accounts.get(acc_id)
        if acc:
            accounts_map[acc_id] = acc

    categories_map = {}
    for cat_id in category_ids:
        cat = uow.categories.get(cat_id)
        if cat:
            categories_map[cat_id] = cat

    lines = []
    for p in postings:
        acc = accounts_map.get(p.account_id)
        cat = categories_map.get(p.category_id) if p.category_id else None

        acc_info = f"({acc.name})" if acc else ""
        cat_info = f"[{cat.name}]" if cat else "[No Category]"
        payee_info = f"Payee: {p.payee}" if p.payee else ""

        # Format: 2025-01-15  EXPENSE  42.50 EUR  [Groceries]  Payee: Lidl  (Cash EUR)
        line = (
            f"{p.posting_date}  {p.posting_type:<7}  {abs(p.amount):>10.2f} "
            f"{acc.currency if acc else '':<3}  {cat_info:<15}  "
            f"{payee_info:<20}  {acc_info}"
        )
        lines.append(line.strip())

    return "\n".join(lines)


def _list_transfers_impl(
    uow: AbstractUnitOfWork,
    *,
    limit: int = 20,
) -> str:
    transfers = services.list_transfers(uow, limit=limit)

    if not transfers:
        return "No transfers found."

    # Sort transfers by date (newest first)
    transfers.sort(key=lambda t: t.transfer_date, reverse=True)

    # Bulk load accounts to avoid N+1 queries
    account_ids = set()
    for t in transfers:
        account_ids.add(t.source_account_id)
        account_ids.add(t.dest_account_id)

    accounts_map = {}
    for acc_id in account_ids:
        acc = uow.accounts.get(acc_id)
        if acc:
            accounts_map[acc_id] = acc

    lines = []
    for t in transfers:
        source = accounts_map.get(t.source_account_id)
        dest = accounts_map.get(t.dest_account_id)

        source_name = source.name if source else "Unknown"
        dest_name = dest.name if dest else "Unknown"
        source_curr = source.currency if source else ""
        dest_curr = dest.currency if dest else ""

        if source_curr == dest_curr:
            amt_str = f"{t.debit_amount} {source_curr}"
        else:
            amt_str = f"{t.debit_amount} {source_curr} → {t.credit_amount} {dest_curr}"

        desc = f" ({t.description})" if t.description else ""
        lines.append(f"{t.transfer_date}  {source_name} → {dest_name}  {amt_str}{desc}")

    return "\n".join(lines)


def _delete_posting_impl(
    uow: AbstractUnitOfWork,
    *,
    posting_id: str,
) -> str:
    try:
        services.delete_posting(uow, posting_id=posting_id)
    except PostingNotFoundError as exc:
        return str(exc)

    return f"Deleted posting '{posting_id}'."


# ── FastMCP instance & tool registration ──────────────────────────────


def _build_auth() -> _BearerTokenVerifier:
    return _BearerTokenVerifier()


@asynccontextmanager
async def _mcp_lifespan(server):
    db = Database()
    db.init()
    try:
        yield {"db": db}
    finally:
        db.dispose()


def _register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools on the given FastMCP instance."""

    @mcp.tool()
    def create_account(
        name: str,
        currency: str,
        initial_balance: str = "0.00",
        is_savings: bool = False,
        ctx: Context | None = None,
    ) -> str:
        """Create a new bank account, checking account, or savings account.

        Args:
            name: Unique name for the account (e.g. 'Main Checking', 'Travel Savings').
            currency: ISO currency code (e.g. 'EUR', 'USD', 'GBP').
            initial_balance: Starting balance as a decimal string (e.g. '1000.00').
            is_savings: Whether this is a savings account (true/false).
        """
        try:
            balance = Decimal(initial_balance)
        except InvalidOperation:
            return f"Invalid initial_balance: '{initial_balance}'. Provide a decimal number."

        with _uow_from_ctx(ctx) as uow:
            return _create_account_impl(
                uow,
                name=name,
                currency=currency,
                initial_balance=balance,
                is_savings=is_savings,
            )

    @mcp.tool()
    def create_category(
        name: str,
        category_type: str,
        parent_name: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Create a new category or subcategory.
        Parents must be created first before subcategories can be added to them.

        Args:
            name: Name of the new category.
            category_type: 'expense' or 'income'.
            parent_name: Optional name of the parent category.
        """
        with _uow_from_ctx(ctx) as uow:
            return _create_category_impl(
                uow,
                name=name,
                category_type_str=category_type,
                parent_name=parent_name,
            )

    @mcp.tool()
    def add_expense(
        amount: str,
        subcategory: str,
        posting_date: str,
        currency: str | None = None,
        account_name: str | None = None,
        payee: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Record an expense. Subcategory must be an existing expense subcategory name.
        Target account can be found by currency or name.

        At least one of currency or account_name must be provided.
        If both are given, account_name takes priority.

        Args:
            amount: The expense amount as a decimal string (e.g. "42.50").
            subcategory: Name of the expense subcategory (e.g. "Groceries").
            posting_date: Date in YYYY-MM-DD format.
            currency: ISO currency code (e.g. "EUR"). Finds first non-savings account.
            account_name: Specific account name (e.g. "Cash EUR").
            payee: Optional payee name.
            description: Optional description.
        """
        try:
            decimal_amount = Decimal(amount)
        except InvalidOperation:
            return f"Invalid amount: '{amount}'. Provide a decimal number."

        try:
            parsed_date = date.fromisoformat(posting_date)
        except ValueError:
            return f"Invalid date: '{posting_date}'. Use YYYY-MM-DD format."

        with _uow_from_ctx(ctx) as uow:
            return _add_expense_impl(
                uow,
                amount=decimal_amount,
                currency=currency,
                account_name=account_name,
                subcategory=subcategory,
                posting_date=parsed_date,
                payee=payee,
                description=description,
            )

    @mcp.tool()
    def add_income(
        amount: str,
        subcategory: str,
        posting_date: str,
        currency: str | None = None,
        account_name: str | None = None,
        payee: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Record income. Subcategory must be an existing income subcategory name.
        Target account can be found by currency or name.

        At least one of currency or account_name must be provided.
        If both are given, account_name takes priority.

        Args:
            amount: The income amount as a decimal string (e.g. "2500.00").
            subcategory: Name of the income subcategory (e.g. "Salary").
            posting_date: Date in YYYY-MM-DD format.
            currency: ISO currency code (e.g. "EUR"). Finds first non-savings account.
            account_name: Specific account name (e.g. "Main Checking").
            payee: Optional payee name.
            description: Optional description.
        """
        try:
            decimal_amount = Decimal(amount)
        except InvalidOperation:
            return f"Invalid amount: '{amount}'. Provide a decimal number."

        try:
            parsed_date = date.fromisoformat(posting_date)
        except ValueError:
            return f"Invalid date: '{posting_date}'. Use YYYY-MM-DD format."

        with _uow_from_ctx(ctx) as uow:
            return _add_income_impl(
                uow,
                amount=decimal_amount,
                currency=currency,
                account_name=account_name,
                subcategory=subcategory,
                posting_date=parsed_date,
                payee=payee,
                description=description,
            )

    @mcp.tool()
    def transfer_funds(
        from_account: str,
        to_account: str,
        amount: str,
        transfer_date: str,
        to_amount: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Transfer money between accounts. Use account names.
        Amounts can differ for cross-currency transfers.

        Args:
            from_account: Source account name.
            to_account: Destination account name.
            amount: Debit amount as a decimal string.
            transfer_date: Date in YYYY-MM-DD format.
            to_amount: Credit amount for cross-currency transfers (defaults to amount).
            description: Optional description.
        """
        try:
            debit = Decimal(amount)
        except InvalidOperation:
            return f"Invalid amount: '{amount}'."

        credit = None
        if to_amount:
            try:
                credit = Decimal(to_amount)
            except InvalidOperation:
                return f"Invalid to_amount: '{to_amount}'."

        try:
            parsed_date = date.fromisoformat(transfer_date)
        except ValueError:
            return f"Invalid date: '{transfer_date}'. Use YYYY-MM-DD format."

        with _uow_from_ctx(ctx) as uow:
            return _transfer_funds_impl(
                uow,
                from_account=from_account,
                to_account=to_account,
                amount=debit,
                to_amount=credit,
                transfer_date=parsed_date,
                description=description,
            )

    @mcp.tool()
    def get_spending(
        period: str = "month",
        reference_date: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Get spending aggregated by parent category.

        Args:
            period: 'week', 'month', or 'year'. Defaults to 'month'.
            reference_date: Reference date in YYYY-MM-DD format to anchor the
                period (defaults to today).
        """
        parsed_reference_date: date | None = None
        if reference_date is not None:
            try:
                parsed_reference_date = date.fromisoformat(reference_date)
            except ValueError:
                return f"Invalid reference_date: '{reference_date}'. Use YYYY-MM-DD format."

        with _uow_from_ctx(ctx) as uow:
            return _get_spending_report_impl(
                uow, period=period, reference_date=parsed_reference_date
            )

    @mcp.tool()
    def list_accounts(
        filter: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """List all accounts with balances.

        Args:
            filter: Use 'savings' to show only savings accounts.
        """
        with _uow_from_ctx(ctx) as uow:
            return _list_accounts_impl(uow, filter=filter)

    @mcp.tool()
    def list_categories(
        category_type: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """List all categories and subcategories.

        Args:
            category_type: Optional filter: 'expense' or 'income'.
        """
        with _uow_from_ctx(ctx) as uow:
            return _list_categories_impl(uow, category_type_str=category_type)

    @mcp.tool()
    def list_postings(
        account_name: str | None = None,
        limit: str = "20",
        ctx: Context | None = None,
    ) -> str:
        """List recent expenses and income postings.

        Args:
            account_name: Optional name of the account to filter by.
            limit: Maximum number of postings to return (default "20", max "100").
        """
        try:
            limit_int = int(limit)
        except ValueError:
            return f"Invalid limit: '{limit}'. Provide an integer."

        if not (1 <= limit_int <= 100):
            return f"Invalid limit: {limit_int}. Must be between 1 and 100."

        with _uow_from_ctx(ctx) as uow:
            return _list_postings_impl(uow, account_name=account_name, limit=limit_int)

    @mcp.tool()
    def list_transfers(
        limit: str = "20",
        ctx: Context | None = None,
    ) -> str:
        """List recent fund transfers between accounts.

        Args:
            limit: Max number of transfers to return (default "20", max "100").
        """
        try:
            limit_int = int(limit)
        except ValueError:
            return f"Invalid limit: '{limit}'. Provide an integer."

        if not (1 <= limit_int <= 100):
            return f"Invalid limit: {limit_int}. Must be between 1 and 100."

        with _uow_from_ctx(ctx) as uow:
            return _list_transfers_impl(uow, limit=limit_int)

    @mcp.tool()
    def delete_posting(
        posting_id: str,
        ctx: Context | None = None,
    ) -> str:
        """Delete a posting (expense or income entry).

        Args:
            posting_id: ID of the posting to delete.
        """
        with _uow_from_ctx(ctx) as uow:
            return _delete_posting_impl(uow, posting_id=posting_id)


def _create_mcp() -> FastMCP:
    mcp = FastMCP(
        "Budget Tracker",
        instructions=(
            "Personal finance assistant. Use these tools to manage your budget: "
            "create accounts, create expense/income categories, record expenses, "
            "record income, transfer funds between accounts, view spending reports, "
            "list accounts with balances, list categories, "
            "list recent postings, list fund transfers, and delete postings."
        ),
        auth=_build_auth(),
        lifespan=_mcp_lifespan,
    )
    _register_tools(mcp)
    return mcp


def create_mcp_app():
    """Create the ASGI app for mounting on FastAPI."""
    mcp = _create_mcp()
    return mcp.http_app(path="/")
