from datetime import date
from decimal import Decimal

from app.domain.exceptions import AccountHasTransfersError
from app.domain.exceptions import AccountHasPostingsError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import CategoryInUseError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import PostingNotFoundError
from app.domain.exceptions import TransferNotFoundError
from app.domain.model import Account
from app.domain.model import Category
from app.domain.model import Posting
from app.domain.model import PostingType
from app.domain.model import Transfer
from app.domain.model import create_transfer as domain_create_transfer
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def get_account(uow: AbstractUnitOfWork, *, account_id: str) -> Account:
    with uow:
        account = uow.repo.get(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")
        return account


def list_accounts(
    uow: AbstractUnitOfWork, *, skip: int = 0, limit: int = 50
) -> list[Account]:
    with uow:
        return uow.repo.list_all(skip=skip, limit=limit)


def update_account_name(
    uow: AbstractUnitOfWork, *, account_id: str, new_name: str
) -> Account:
    with uow:
        account = uow.repo.get(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")

        existing_account = uow.repo.get_by_name(new_name)
        if existing_account and existing_account.account_id != account_id:
            raise DuplicateAccountNameError(
                f"Account with name '{new_name}' already exists"
            )

        account.name = new_name
        uow.commit()
        logger.info("Updated account name for id: %s to '%s'", account_id, new_name)
        return account


def create_account(
    uow: AbstractUnitOfWork,
    *,
    name: str,
    currency: str,
    initial_balance: Decimal,
) -> Account:
    with uow:
        # Validate initial balance is non-negative
        if initial_balance < 0:
            raise InvalidInitialBalanceError(
                f"Initial balance cannot be negative, got {initial_balance}"
            )

        # Check for duplicate account name
        existing_account = uow.repo.get_by_name(name)
        if existing_account:
            raise DuplicateAccountNameError(f"Account with name '{name}' already exists")

        new_account = Account(
            account_id=None,
            name=name,
            currency=currency,
            initial_balance=initial_balance,
        )
        uow.repo.add(new_account)
        uow.commit()
        logger.info(
            "Created account: %s (currency: %s, initial_balance: %s)",
            new_account.name,
            new_account.currency,
            new_account.initial_balance,
        )

        return new_account


def delete_account(uow: AbstractUnitOfWork, *, account_id: str) -> None:
    with uow:
        # Check if account exists
        account = uow.repo.get(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")

        # Check if account has transfers
        transfers = uow.repo.list_transfers_for_account(account_id)
        if transfers:
            raise AccountHasTransfersError(
                f"Cannot delete account '{account.name}': "
                f"has {len(transfers)} transfer(s)"
            )

        # Check if account has postings
        posting_count = uow.repo.count_postings_for_account(account_id)
        if posting_count > 0:
            raise AccountHasPostingsError(
                f"Cannot delete account '{account.name}': has {posting_count} posting(s)"
            )

        uow.repo.delete(account)
        uow.commit()
        logger.info("Deleted account id: %s", account_id)


def create_posting(
    uow: AbstractUnitOfWork,
    *,
    account_id: str,
    amount: Decimal,
    posting_date: date,
    posting_type: PostingType,
    category_id: str | None = None,
) -> Posting:
    with uow:
        account = uow.repo.get(account_id)
        if not account:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")

        if category_id:
            category = uow.repo.get_category(category_id)
            if not category:
                raise CategoryNotFoundError(
                    f"Category with id '{category_id}' not found"
                )

        posting = account.record_posting(
            amount=amount,
            posting_date=posting_date,
            category_id=category_id,
            posting_type=posting_type,
        )
        uow.commit()
        logger.info(
            "Created %s posting for account %s: %s",
            posting_type,
            account_id,
            posting.amount,
        )
        return posting


def get_posting(uow: AbstractUnitOfWork, *, posting_id: str) -> Posting:
    with uow:
        posting = uow.repo.get_posting(posting_id)
        if posting is None:
            raise PostingNotFoundError(f"Posting with id '{posting_id}' not found")
        return posting


def list_postings(
    uow: AbstractUnitOfWork,
    *,
    account_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Posting]:
    with uow:
        return uow.repo.list_postings(account_id=account_id, skip=skip, limit=limit)


# Category Services


def create_category(
    uow: AbstractUnitOfWork,
    *,
    name: str,
) -> Category:
    with uow:
        # Check for duplicate name
        existing_category = uow.repo.get_category_by_name(name)
        if existing_category:
            raise DuplicateCategoryNameError(
                f"Category with name '{name}' already exists"
            )

        new_category = Category(
            category_id=None,
            name=name,
        )
        uow.repo.add_category(new_category)
        uow.commit()
        logger.info("Created category: %s", name)
        return new_category


def list_categories(
    uow: AbstractUnitOfWork, skip: int = 0, limit: int = 50
) -> list[Category]:
    with uow:
        return uow.repo.list_categories(skip=skip, limit=limit)


def update_category_name(
    uow: AbstractUnitOfWork, *, category_id: str, new_name: str
) -> Category:
    with uow:
        category = uow.repo.get_category(category_id)
        if category is None:
            raise CategoryNotFoundError(f"Category with id '{category_id}' not found")

        existing_category = uow.repo.get_category_by_name(new_name)
        if existing_category and existing_category.category_id != category_id:
            raise DuplicateCategoryNameError(
                f"Category with name '{new_name}' already exists"
            )

        category.name = new_name
        uow.commit()
        return category


def delete_category(uow: AbstractUnitOfWork, *, category_id: str) -> None:
    with uow:
        category = uow.repo.get_category(category_id)
        if category is None:
            raise CategoryNotFoundError(f"Category with id '{category_id}' not found")

        # Check usage
        if uow.repo.count_postings_for_category(category_id) > 0:
            raise CategoryInUseError(
                f"Category '{category.name}' has postings and cannot be deleted"
            )

        uow.repo.delete_category(category)
        uow.commit()
        logger.info("Deleted category id: %s", category_id)


# Transfer Services


def create_transfer(
    uow: AbstractUnitOfWork,
    *,
    source_account_id: str,
    dest_account_id: str,
    debit_amount: Decimal,
    credit_amount: Decimal,
    transfer_date: date,
    description: str | None = None,
) -> Transfer:
    with uow:
        source_account = uow.repo.get(source_account_id)
        if not source_account:
            raise AccountNotFoundError(
                f"Source account with id '{source_account_id}' not found"
            )

        dest_account = uow.repo.get(dest_account_id)
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

        uow.repo.add_transfer(transfer)
        uow.commit()
        logger.info(
            "Created transfer from %s to %s: %s (debit) / %s (credit)",
            source_account_id,
            dest_account_id,
            debit_amount,
            credit_amount,
        )
        return transfer


def get_transfer(uow: AbstractUnitOfWork, *, transfer_id: str) -> Transfer:
    with uow:
        transfer = uow.repo.get_transfer(transfer_id)
        if transfer is None:
            raise TransferNotFoundError(f"Transfer with id '{transfer_id}' not found")
        return transfer


def list_transfers(
    uow: AbstractUnitOfWork, skip: int = 0, limit: int = 50
) -> list[Transfer]:
    with uow:
        return uow.repo.list_transfers(skip=skip, limit=limit)
