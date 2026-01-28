from decimal import Decimal

from app.domain.model import Account
from app.domain.model import Category
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import CategoryInUseError

from app.service_layer.abstract_repository import AbstractRepository


def get_account(repo: AbstractRepository, *, account_id: str) -> Account:
    account = repo.get(account_id)
    if account is None:
        raise AccountNotFoundError(f"Account with id '{account_id}' not found")
    return account


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
    account = repo.get(account_id)
    if account is None:
        raise AccountNotFoundError(f"Account with id '{account_id}' not found")

    # Check if account has transfers
    transfers = repo.list_transfers_for_account(account_id)
    if transfers:
        raise AccountHasTransfersError(
            f"Cannot delete account '{account.name}': has {len(transfers)} transfer(s)"
        )

    repo.delete(account)
    repo.commit()


# Category Services


def create_category(
    repo: AbstractRepository,
    *,
    name: str,
) -> Category:
    # Check for duplicate name
    existing_category = repo.get_category_by_name(name)
    if existing_category:
        raise DuplicateCategoryNameError(f"Category with name '{name}' already exists")

    new_category = Category(
        category_id=None,
        name=name,
    )
    repo.add_category(new_category)
    repo.commit()
    return new_category


def list_categories(repo: AbstractRepository) -> list[Category]:
    return repo.list_categories()


def delete_category(repo: AbstractRepository, *, category_id: str) -> None:
    category = repo.get_category(category_id)
    if category is None:
        raise CategoryNotFoundError(f"Category with id '{category_id}' not found")

    # Check usage
    if repo.count_postings_for_category(category_id) > 0:
        raise CategoryInUseError(
            f"Category '{category.name}' has postings and cannot be deleted"
        )

    repo.delete_category(category)
    repo.commit()
