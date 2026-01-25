from decimal import Decimal

from app.domain.model import Account
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError

from app.service_layer.abstract_repository import AbstractRepository


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
        account_id=None,
        name=name,
        currency=currency,
        initial_balance=initial_balance,
    )
    repo.add(new_account)
    repo.commit()

    return new_account


def delete_account(repo: AbstractRepository, *, account_id: str) -> None:
    # Check if account exists
    try:
        account = repo.get(account_id)
    except Exception:
        raise AccountNotFoundError(f"Account with id '{account_id}' not found")

    # Check if account has transfers
    transfers = repo.list_transfers_for_account(account_id)
    if transfers:
        raise AccountHasTransfersError(
            f"Cannot delete account '{account.name}': has {len(transfers)} transfer(s)"
        )

    repo.delete(account)
    repo.commit()
