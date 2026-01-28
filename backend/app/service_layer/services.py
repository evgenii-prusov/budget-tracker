from decimal import Decimal

from app.domain.model import Account
from app.domain.model import Category
from app.domain.model import Posting
from app.domain.model import PostingType
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import CategoryInUseError
from app.domain.exceptions import PostingNotFoundError

from app.service_layer.abstract_repository import AbstractRepository
from datetime import date


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


def create_posting(
    repo: AbstractRepository,
    *,
    account_id: str,
    amount: Decimal,
    posting_date: date,
    posting_type: PostingType,
    category_id: str | None = None,
) -> Posting:
    account = repo.get(account_id)
    if not account:
        raise AccountNotFoundError(f"Account with id '{account_id}' not found")

    if category_id:
        category = repo.get_category(category_id)
        if not category:
            raise CategoryNotFoundError(f"Category with id '{category_id}' not found")

    posting = account.record_posting(
        amount=amount,
        posting_date=posting_date,
        category_id=category_id,
        posting_type=posting_type,
    )
    repo.commit()
    return posting


def get_posting(repo: AbstractRepository, *, posting_id: str) -> Posting:
    posting = repo.get_posting(posting_id)
    if posting is None:
        raise PostingNotFoundError(f"Posting with id '{posting_id}' not found")
    return posting


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
