from decimal import Decimal
from datetime import date

from app.domain.model import Account
from app.domain.model import Category
from app.domain.model import Posting
from app.domain.model import PostingType
from app.domain.model import Transfer
from app.domain.model import create_transfer as domain_create_transfer
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import CategoryInUseError
from app.domain.exceptions import PostingNotFoundError
from app.domain.exceptions import TransferNotFoundError

from app.service_layer.abstract_repository import AbstractRepository


def get_account(repo: AbstractRepository, *, account_id: str) -> Account:
    account = repo.get(account_id)
    if account is None:
        raise AccountNotFoundError(f"Account with id '{account_id}' not found")
    return account


def update_account_name(
    repo: AbstractRepository, *, account_id: str, new_name: str
) -> Account:
    account = repo.get(account_id)
    if account is None:
        raise AccountNotFoundError(f"Account with id '{account_id}' not found")

    existing_account = repo.get_by_name(new_name)
    if existing_account and existing_account.account_id != account_id:
        raise DuplicateAccountNameError(f"Account with name '{new_name}' already exists")

    account.name = new_name
    repo.commit()
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


def list_postings(
    repo: AbstractRepository, *, account_id: str | None = None
) -> list[Posting]:
    return repo.list_postings(account_id=account_id)


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


def update_category_name(
    repo: AbstractRepository, *, category_id: str, new_name: str
) -> Category:
    category = repo.get_category(category_id)
    if category is None:
        raise CategoryNotFoundError(f"Category with id '{category_id}' not found")

    existing_category = repo.get_category_by_name(new_name)
    if existing_category and existing_category.category_id != category_id:
        raise DuplicateCategoryNameError(
            f"Category with name '{new_name}' already exists"
        )

    category.name = new_name
    repo.commit()
    return category


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


# Transfer Services


def create_transfer(
    repo: AbstractRepository,
    *,
    source_account_id: str,
    dest_account_id: str,
    debit_amount: Decimal,
    credit_amount: Decimal,
    transfer_date: date,
    description: str | None = None,
) -> Transfer:
    source_account = repo.get(source_account_id)
    if not source_account:
        raise AccountNotFoundError(
            f"Source account with id '{source_account_id}' not found"
        )

    dest_account = repo.get(dest_account_id)
    if not dest_account:
        raise AccountNotFoundError(
            f"Destination account with id '{dest_account_id}' not found"
        )

    transfer = domain_create_transfer(
        source=source_account,
        dest=dest_account,
        transfer_date=transfer_date,
        debit_amount=debit_amount,
        credit_amount=credit_amount,
        description=description,
    )

    repo.add_transfer(transfer)
    repo.commit()
    return transfer


def get_transfer(repo: AbstractRepository, *, transfer_id: str) -> Transfer:
    transfer = repo.get_transfer(transfer_id)
    if transfer is None:
        raise TransferNotFoundError(f"Transfer with id '{transfer_id}' not found")
    return transfer


def list_transfers(repo: AbstractRepository) -> list[Transfer]:
    return repo.list_transfers()
