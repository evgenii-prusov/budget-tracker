"""MCP Server for budget-tracker.

Exposes 4 tools: add_expense, transfer_funds, get_spending_report, list_accounts.
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
from app.domain.exceptions import InsufficientFundsError
from app.domain.model import PostingType
from app.mcp.resolvers import (
    resolve_account_by_currency,
    resolve_account_by_name,
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


def _add_expense_impl(
    uow: AbstractUnitOfWork,
    *,
    amount: Decimal,
    currency: str,
    subcategory: str,
    posting_date: date,
    payee: str | None = None,
    description: str | None = None,
) -> str:
    try:
        account = resolve_account_by_currency(uow, currency)
        category = resolve_subcategory_by_name(uow, subcategory)
    except ValueError as exc:
        return str(exc)

    try:
        posting = services.create_posting(
            uow,
            account_id=account.account_id,
            amount=amount,
            posting_date=posting_date,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
            payee=payee,
            description=description,
        )
    except InsufficientFundsError as exc:
        return str(exc)

    return (
        f"Recorded expense of {abs(posting.amount)} {account.currency} "
        f"on {account.name} under {subcategory}."
        + (f" Payee: {payee}." if payee else "")
        + f" New balance: {account.balance} {account.currency}."
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
    except InsufficientFundsError as exc:
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
    def add_expense(
        amount: str,
        currency: str,
        subcategory: str,
        posting_date: str,
        payee: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Record an expense. Finds account by currency (prefers non-savings).
        Subcategory must be an existing expense subcategory name.

        Args:
            amount: The expense amount as a decimal string (e.g. "42.50").
            currency: ISO currency code (e.g. "EUR", "USD").
            subcategory: Name of the expense subcategory (e.g. "Groceries").
            posting_date: Date in YYYY-MM-DD format.
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
        ctx: Context | None = None,
    ) -> str:
        """Get spending aggregated by parent category.

        Args:
            period: 'week', 'month', or 'year'. Defaults to 'month'.
        """
        with _uow_from_ctx(ctx) as uow:
            return _get_spending_report_impl(uow, period=period)

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


def _create_mcp() -> FastMCP:
    mcp = FastMCP(
        "Budget Tracker",
        instructions=(
            "Personal finance assistant. Use these tools to record expenses, "
            "transfer funds between accounts, view spending reports, and list accounts."
        ),
        auth=_build_auth(),
        lifespan=_mcp_lifespan,
    )
    _register_tools(mcp)
    return mcp


def create_mcp_app():
    """Create the ASGI app for mounting on FastAPI."""
    mcp = _create_mcp()
    return mcp.http_app()
