from datetime import date
from decimal import Decimal

from app.domain.exceptions import AccountHasTransfersError
from app.domain.exceptions import AccountHasPostingsError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import CategoryHasChildrenError
from app.domain.exceptions import CategoryHierarchyError
from app.domain.exceptions import CategoryInUseError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import ParentCategoryPostingError
from app.domain.exceptions import PostingNotFoundError
from app.domain.exceptions import TransferNotFoundError
from app.domain.model import Account
from app.domain.model import Category
from app.domain.model import CategoryType
from app.domain.model import Posting
from app.domain.model import PostingType
from app.domain.model import Transfer
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def get_account(uow: AbstractUnitOfWork, *, account_id: str) -> Account:
    with uow:
        account = uow.accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")
        return account


def list_accounts(uow: AbstractUnitOfWork, *, skip: int = 0, limit: int = 50) -> list[Account]:
    with uow:
        return uow.accounts.list_all(skip=skip, limit=limit)


def update_account_name(uow: AbstractUnitOfWork, *, account_id: str, new_name: str) -> Account:
    with uow:
        account = uow.accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")

        existing_account = uow.accounts.get_by_name(new_name)
        if existing_account and existing_account.account_id != account_id:
            raise DuplicateAccountNameError(f"Account with name '{new_name}' already exists")

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
    is_savings: bool = False,
    description: str | None = None,
) -> Account:
    with uow:
        if initial_balance < 0:
            raise InvalidInitialBalanceError(
                f"Initial balance cannot be negative, got {initial_balance}"
            )

        existing_account = uow.accounts.get_by_name(name)
        if existing_account:
            raise DuplicateAccountNameError(f"Account with name '{name}' already exists")

        new_account = Account(
            account_id=None,
            name=name,
            currency=currency,
            initial_balance=initial_balance,
            is_savings=is_savings,
            description=description,
        )
        uow.accounts.add(new_account)
        uow.commit()
        logger.info(
            "Created account: %s (currency: %s, initial_balance: %s)",
            new_account.name,
            new_account.currency,
            new_account.initial_balance,
        )

        return new_account


def update_account_description(
    uow: AbstractUnitOfWork, *, account_id: str, description: str | None
) -> Account:
    with uow:
        account = uow.accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")

        account.description = description
        uow.commit()
        logger.info("Updated account description for id: %s", account_id)
        return account


def delete_account(uow: AbstractUnitOfWork, *, account_id: str) -> None:
    with uow:
        account = uow.accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")

        posting_count = account.posting_count
        transfer_count = account.transfer_count

        if posting_count > 0 and transfer_count > 0:
            raise AccountHasPostingsError(
                f"Cannot delete account '{account.name}': "
                f"has {posting_count} posting(s) and {transfer_count} transfer(s)"
            )

        if posting_count > 0:
            raise AccountHasPostingsError(
                f"Cannot delete account '{account.name}': has {posting_count} posting(s)"
            )

        if transfer_count > 0:
            raise AccountHasTransfersError(
                f"Cannot delete account '{account.name}': has {transfer_count} transfer(s)"
            )

        uow.accounts.delete(account)
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
    payee: str | None = None,
    description: str | None = None,
) -> Posting:
    with uow:
        account = uow.accounts.get(account_id)
        if not account:
            raise AccountNotFoundError(f"Account with id '{account_id}' not found")

        if category_id:
            category = uow.categories.get(category_id)
            if not category:
                raise CategoryNotFoundError(f"Category with id '{category_id}' not found")
            if category.parent_id is None:
                raise ParentCategoryPostingError(
                    f"Cannot create posting with parent category '{category.name}'. "
                    f"Use a subcategory instead."
                )
            if str(posting_type) != str(category.category_type):
                raise CategoryHierarchyError(
                    f"Posting type '{posting_type}' does not match "
                    f"category type '{category.category_type}'"
                )

        posting = account.record_posting(
            amount=amount,
            posting_date=posting_date,
            category_id=category_id,
            posting_type=posting_type,
            payee=payee,
            description=description,
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
        account = uow.accounts.get_by_posting_id(posting_id)
        if account is None:
            raise PostingNotFoundError(f"Posting with id '{posting_id}' not found")
        posting = account.get_posting(posting_id)
        assert posting is not None
        return posting


def list_postings(
    uow: AbstractUnitOfWork,
    *,
    account_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Posting]:
    with uow:
        if account_id is not None:
            account = uow.accounts.get(account_id)
            if account is None:
                return []
            return account.postings[skip : skip + limit]
        else:
            all_postings: list[Posting] = []
            for account in uow.accounts.list_all():
                all_postings.extend(account.postings)
            return all_postings[skip : skip + limit]


def delete_posting(uow: AbstractUnitOfWork, *, posting_id: str) -> None:
    with uow:
        found = uow.accounts.delete_posting_by_id(posting_id)
        if not found:
            raise PostingNotFoundError(f"Posting with id '{posting_id}' not found")
        uow.commit()
        logger.info("Deleted posting id: %s", posting_id)


# Category Services


def create_category(
    uow: AbstractUnitOfWork,
    *,
    name: str,
    category_type: CategoryType,
    parent_id: str | None = None,
) -> Category:
    with uow:
        if parent_id is not None:
            parent = uow.categories.get(parent_id)
            if parent is None:
                raise CategoryNotFoundError(f"Parent category with id '{parent_id}' not found")
            if parent.parent_id is not None:
                raise CategoryHierarchyError(
                    "Cannot create subcategory of a subcategory (max 2 levels)"
                )
            if parent.category_type != category_type:
                raise CategoryHierarchyError(
                    f"Subcategory type '{category_type}' must match "
                    f"parent type '{parent.category_type}'"
                )

        existing_category = uow.categories.get_by_name(name, parent_id=parent_id)
        if existing_category:
            raise DuplicateCategoryNameError(f"Category with name '{name}' already exists")

        new_category = Category(
            category_id=None,
            name=name,
            category_type=category_type,
            parent_id=parent_id,
        )
        uow.categories.add(new_category)
        uow.commit()
        logger.info("Created category: %s", name)
        return new_category


def get_category(uow: AbstractUnitOfWork, *, category_id: str) -> Category:
    with uow:
        category = uow.categories.get(category_id)
        if category is None:
            raise CategoryNotFoundError(f"Category with id '{category_id}' not found")
        return category


def list_categories(uow: AbstractUnitOfWork, skip: int = 0, limit: int = 50) -> list[Category]:
    with uow:
        return uow.categories.list_all(skip=skip, limit=limit)


def update_category_name(uow: AbstractUnitOfWork, *, category_id: str, new_name: str) -> Category:
    with uow:
        category = uow.categories.get(category_id)
        if category is None:
            raise CategoryNotFoundError(f"Category with id '{category_id}' not found")

        existing_category = uow.categories.get_by_name(new_name, parent_id=category.parent_id)
        if existing_category and existing_category.category_id != category_id:
            raise DuplicateCategoryNameError(f"Category with name '{new_name}' already exists")

        category.name = new_name
        uow.commit()
        return category


def delete_category(uow: AbstractUnitOfWork, *, category_id: str) -> None:
    with uow:
        category = uow.categories.get(category_id)
        if category is None:
            raise CategoryNotFoundError(f"Category with id '{category_id}' not found")

        if category.parent_id is None and uow.categories.count_children(category_id) > 0:
            raise CategoryHasChildrenError(
                f"Cannot delete parent category '{category.name}': has child categories"
            )

        if uow.categories.count_postings(category_id) > 0:
            raise CategoryInUseError(
                f"Category '{category.name}' has postings and cannot be deleted"
            )

        uow.categories.delete(category)
        uow.commit()
        logger.info("Deleted category id: %s", category_id)


def list_parent_categories(
    uow: AbstractUnitOfWork, skip: int = 0, limit: int = 50
) -> list[Category]:
    with uow:
        return uow.categories.list_parents(skip=skip, limit=limit)


def list_subcategories(uow: AbstractUnitOfWork, *, parent_id: str) -> list[Category]:
    with uow:
        return uow.categories.list_children(parent_id)


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
        source_account = uow.accounts.get(source_account_id)
        if not source_account:
            raise AccountNotFoundError(f"Source account with id '{source_account_id}' not found")

        dest_account = uow.accounts.get(dest_account_id)
        if not dest_account:
            raise AccountNotFoundError(f"Destination account with id '{dest_account_id}' not found")

        transfer = Transfer(
            transfer_id=None,
            source_account_id=source_account_id,
            dest_account_id=dest_account_id,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            transfer_date=transfer_date,
            description=description,
        )

        source_account.record_outgoing_transfer(transfer)
        dest_account.record_incoming_transfer(transfer)
        uow.transfers.add(transfer)

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
        transfer = uow.transfers.get(transfer_id)
        if transfer is None:
            raise TransferNotFoundError(f"Transfer with id '{transfer_id}' not found")
        return transfer


def list_transfers(uow: AbstractUnitOfWork, *, skip: int = 0, limit: int = 50) -> list[Transfer]:
    with uow:
        return uow.transfers.list_all(skip, limit)


def delete_transfer(uow: AbstractUnitOfWork, *, transfer_id: str) -> None:
    with uow:
        transfer = uow.transfers.get(transfer_id)
        if transfer is None:
            raise TransferNotFoundError(f"Transfer with id '{transfer_id}' not found")

        source_account = uow.accounts.get(transfer.source_account_id)
        dest_account = uow.accounts.get(transfer.dest_account_id)

        if source_account:
            source_account.remove_outgoing_transfer(transfer_id)
        if dest_account:
            dest_account.remove_incoming_transfer(transfer_id)

        uow.transfers.delete(transfer)
        uow.commit()
        logger.info("Deleted transfer id: %s", transfer_id)
