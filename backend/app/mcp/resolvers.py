"""Name-to-ID resolution helpers for MCP tools.

LLM assistants use human-friendly names (e.g. "Cash EUR", "Groceries"),
not UUIDs. These resolvers bridge the gap and provide helpful error
messages listing available options so the LLM can suggest corrections.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.model import Account, Category, CategoryType

if TYPE_CHECKING:
    from app.service_layer.unit_of_work import AbstractUnitOfWork


def resolve_account_by_name(uow: AbstractUnitOfWork, name: str) -> Account:
    """Find an account by exact name (case-insensitive)."""
    all_accounts = uow.accounts.list_all(skip=0, limit=200)
    for acc in all_accounts:
        if acc.name.lower() == name.lower():
            return acc

    available = ", ".join(a.name for a in all_accounts)
    raise ValueError(f"No account named '{name}'. Available: [{available}]")


def resolve_account_by_currency(uow: AbstractUnitOfWork, currency: str) -> Account:
    """Find an account by currency code (case-insensitive), preferring non-savings."""
    currency_upper = currency.upper()
    all_accounts = uow.accounts.list_all(skip=0, limit=200)

    matches = [a for a in all_accounts if a.currency == currency_upper]
    if not matches:
        available = ", ".join(sorted({a.currency for a in all_accounts}))
        raise ValueError(
            f"No account with currency '{currency_upper}'. Available currencies: [{available}]"
        )

    # Prefer non-savings accounts
    non_savings = [a for a in matches if not a.is_savings]
    return non_savings[0] if non_savings else matches[0]


def resolve_subcategory_by_name(
    uow: AbstractUnitOfWork,
    name: str,
    category_type: CategoryType | None = None,
) -> Category:
    """Find a subcategory by name (case-insensitive). Ignores parent categories."""
    all_categories = uow.categories.list_all(skip=0, limit=500)
    subcategories = [c for c in all_categories if c.parent_id is not None]

    if category_type is not None:
        subcategories = [c for c in subcategories if c.category_type == category_type]

    for cat in subcategories:
        if cat.name.lower() == name.lower():
            return cat

    type_hint = f" (type={category_type.value})" if category_type is not None else ""
    available = ", ".join(c.name for c in subcategories)
    raise ValueError(f"No subcategory named '{name}'{type_hint}. Available: [{available}]")
