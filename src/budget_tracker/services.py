from decimal import Decimal

from budget_tracker.model import (
    Account,
    DuplicateAccountNameError,
    InvalidInitialBalanceError,
)
from budget_tracker.repository import AbstractRepository


def create_account(
    repo: AbstractRepository,
    *,
    name: str,
    currency: str,
    initial_balance: Decimal,
) -> Account:
    # Validate initial balance is non-negative
    if initial_balance < 0:
        raise InvalidInitialBalanceError(
            f"Initial balance cannot be negative, got {initial_balance}"
        )

    # Check for duplicate account name
    existing_account = repo.get_by_name(name)
    if existing_account:
        raise DuplicateAccountNameError(f"Account with name '{name}' already exists")

    new_account = Account(
        id=None,
        name=name,
        currency=currency,
        initial_balance=initial_balance,
    )
    repo.add(new_account)
    repo.commit()

    return new_account
