import pytest
from decimal import Decimal
from datetime import date

from app.domain.model import Account
from app.domain.model import Transfer
from app.domain.model import PostingType
from app.domain.model import CategoryType
from app.domain.model import Category
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError
from app.domain.exceptions import AccountHasPostingsError
from app.domain.exceptions import CategoryHasChildrenError
from app.domain.exceptions import CategoryHierarchyError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import InsufficientFundsError
from app.domain.exceptions import ParentCategoryPostingError
from app.domain.exceptions import PostingNotFoundError
from app.domain.exceptions import TransferNotFoundError

from collections.abc import Callable

from app.service_layer.abstract_account_repository import AbstractAccountRepository
from app.service_layer.abstract_transfer_repository import AbstractTransferRepository
from app.service_layer.abstract_category_repository import AbstractCategoryRepository
from app.service_layer.abstract_report_repository import AbstractReportRepository
from app.service_layer.reports import SpendingReport
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.service_layer.services import create_account
from app.service_layer.services import delete_account
from app.service_layer.services import create_category
from app.service_layer.services import delete_category
from app.service_layer.services import get_category
from app.service_layer.services import list_parent_categories
from app.service_layer.services import list_subcategories
from app.service_layer.services import create_posting
from app.service_layer.services import delete_posting
from app.service_layer.services import get_posting
from app.service_layer.services import list_postings
from app.service_layer.services import update_account
from app.service_layer.services import create_transfer
from app.service_layer.services import delete_transfer
from app.service_layer.services import get_transfer
from app.service_layer.services import list_transfers
from tests.constants import JAN_01


class FakeAccountRepository(AbstractAccountRepository):
    def __init__(self):
        self._accounts: list[Account] = []

    def add(self, account: Account) -> None:
        self._accounts.append(account)

    def get(self, account_id: str) -> Account | None:
        return next((a for a in self._accounts if a.account_id == account_id), None)

    def get_by_name(self, name: str) -> Account | None:
        return next((a for a in self._accounts if a.name == name), None)

    def get_by_posting_id(self, posting_id: str) -> Account | None:
        for acc in self._accounts:
            if acc.get_posting(posting_id) is not None:
                return acc
        return None

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Account]:
        return list(self._accounts)[skip : skip + limit]

    def delete(self, account: Account) -> None:
        self._accounts.remove(account)

    def delete_posting_by_id(self, posting_id: str) -> bool:
        for acc in self._accounts:
            posting = acc.get_posting(posting_id)
            if posting is not None:
                acc.remove_posting(posting_id)
                return True
        return False


class FakeTransferRepository(AbstractTransferRepository):
    def __init__(self):
        self._transfers: list[Transfer] = []

    def add(self, transfer: Transfer) -> None:
        self._transfers.append(transfer)

    def get(self, transfer_id: str) -> Transfer | None:
        return next((t for t in self._transfers if t.transfer_id == transfer_id), None)

    def delete(self, transfer: Transfer) -> None:
        self._transfers.remove(transfer)

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Transfer]:
        return list(self._transfers)[skip : skip + limit]


class FakeCategoryRepository(AbstractCategoryRepository):
    def __init__(self, count_postings_fn: Callable[[str], int] | None = None):
        self._categories: list[Category] = []
        self._count_postings_fn = count_postings_fn or (lambda _: 0)

    def add(self, category: Category) -> None:
        self._categories.append(category)
        if category.parent_id:
            parent = self.get(category.parent_id)
            if parent:
                parent.children.append(category)

    def get(self, category_id: str) -> Category | None:
        return next((c for c in self._categories if c.category_id == category_id), None)

    def get_by_name(self, name: str, parent_id: str | None = None) -> Category | None:
        return next(
            (c for c in self._categories if c.name == name and c.parent_id == parent_id),
            None,
        )

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Category]:
        return list(self._categories)[skip : skip + limit]

    def list_parents(self, skip: int = 0, limit: int = 50) -> list[Category]:
        parents = [c for c in self._categories if c.parent_id is None]
        return parents[skip : skip + limit]

    def list_children(self, parent_id: str) -> list[Category]:
        return [c for c in self._categories if c.parent_id == parent_id]

    def count_children(self, category_id: str) -> int:
        return len([c for c in self._categories if c.parent_id == category_id])

    def delete(self, category: Category) -> None:
        self._categories.remove(category)

    def count_postings(self, category_id: str) -> int:
        return self._count_postings_fn(category_id)


class FakeReportRepository(AbstractReportRepository):
    def __init__(self):
        pass

    def spending_by_period(
        self, start_date: date, end_date: date, exclude_savings: bool = True
    ) -> SpendingReport:
        return SpendingReport(period="month", start_date=start_date, end_date=end_date, rows=[])


class FakeUnitOfWork(AbstractUnitOfWork):
    accounts: FakeAccountRepository
    transfers: FakeTransferRepository
    categories: FakeCategoryRepository
    reports: FakeReportRepository

    def __init__(self):
        self.accounts = FakeAccountRepository()
        self.transfers = FakeTransferRepository()
        self.reports = FakeReportRepository()
        self.committed = False

        # Wire up category's count_postings to scan accounts
        def _count_postings_fn(category_id: str) -> int:
            count = 0
            for acc in self.accounts._accounts:
                for p in acc.postings:
                    if p.category_id == category_id:
                        count += 1
            return count

        self.categories = FakeCategoryRepository(_count_postings_fn)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


class TestCreateAccount:
    def test_create_account_success(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        assert account.name == "Test Account"
        assert account.currency == "USD"
        assert account.initial_balance == Decimal(100)
        assert uow.committed is True
        assert len(uow.accounts._accounts) == 1

    def test_create_account_with_zero_balance(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Zero Balance",
            currency="EUR",
            initial_balance=Decimal(0),
        )
        assert account.initial_balance == Decimal(0)
        assert uow.committed is True

    def test_create_account_duplicate_name_raises_error(self):
        uow = FakeUnitOfWork()
        create_account(
            uow,
            name="Existing Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        with pytest.raises(DuplicateAccountNameError) as exc_info:
            create_account(
                uow,
                name="Existing Account",
                currency="EUR",
                initial_balance=Decimal(0),
            )

        assert "already exists" in str(exc_info.value)
        assert "Existing Account" in str(exc_info.value)
        assert uow.committed is False

    def test_create_account_with_is_savings(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Savings Account",
            currency="USD",
            initial_balance=Decimal(100),
            is_savings=True,
        )
        assert account.is_savings is True
        assert uow.committed is True

    def test_create_account_negative_balance_raises_error(self):
        uow = FakeUnitOfWork()
        with pytest.raises(InvalidInitialBalanceError) as exc_info:
            create_account(
                uow,
                name="Negative Account",
                currency="USD",
                initial_balance=Decimal(-100),
            )

        assert "cannot be negative" in str(exc_info.value)
        assert "-100" in str(exc_info.value)
        assert uow.committed is False
        assert len(uow.accounts._accounts) == 0


class TestUpdateAccountName:
    def test_update_account_name_success(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Old Name",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        updated_account = update_account(
            uow,
            account_id=account.account_id,
            name="New Name",
        )

        assert updated_account.name == "New Name"
        assert uow.committed is True

    def test_update_account_name_duplicate_name_raises_error(self):
        uow = FakeUnitOfWork()
        account1 = create_account(
            uow,
            name="Account 1",
            currency="USD",
            initial_balance=Decimal(100),
        )
        create_account(
            uow,
            name="Account 2",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        with pytest.raises(DuplicateAccountNameError) as exc_info:
            update_account(
                uow,
                account_id=account1.account_id,
                name="Account 2",
            )

        assert "already exists" in str(exc_info.value)
        assert uow.committed is False
        assert account1.name == "Account 1"

    def test_update_account_name_not_found_raises_error(self):
        uow = FakeUnitOfWork()
        with pytest.raises(AccountNotFoundError) as exc_info:
            update_account(
                uow,
                account_id="nonexistent-id",
                name="New Name",
            )

        assert "not found" in str(exc_info.value)
        assert uow.committed is False


class TestCreateAccountDescription:
    def test_create_account_with_description(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="My Account",
            currency="USD",
            initial_balance=Decimal(0),
            description="My main spending account",
        )
        assert account.description == "My main spending account"

    def test_create_account_description_defaults_to_none(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="My Account",
            currency="USD",
            initial_balance=Decimal(0),
        )
        assert account.description is None


class TestUpdateAccountDescription:
    def test_update_account_description_success(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="My Account",
            currency="USD",
            initial_balance=Decimal(0),
        )
        uow.committed = False

        updated = update_account(
            uow,
            account_id=account.account_id,
            description="Updated description",
            update_description=True,
        )

        assert updated.description == "Updated description"
        assert uow.committed is True

    def test_update_account_description_to_none(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="My Account",
            currency="USD",
            initial_balance=Decimal(0),
            description="Old description",
        )
        uow.committed = False

        updated = update_account(
            uow,
            account_id=account.account_id,
            description=None,
            update_description=True,
        )

        assert updated.description is None
        assert uow.committed is True

    def test_update_account_description_not_found_raises_error(self):
        uow = FakeUnitOfWork()
        with pytest.raises(AccountNotFoundError):
            update_account(
                uow,
                account_id="nonexistent-id",
                description="Some description",
                update_description=True,
            )
        assert uow.committed is False


class TestDeleteAccount:
    def test_delete_account_success(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        delete_account(uow, account_id=account.account_id)

        assert uow.committed is True
        assert len(uow.accounts._accounts) == 0

    def test_delete_account_with_postings_raises_error(self):
        """Service prevents deletion when account has postings."""
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(100),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )
        uow.committed = False

        with pytest.raises(AccountHasPostingsError) as exc:
            delete_account(uow, account_id=account.account_id)

        assert "Cannot delete" in str(exc.value)
        assert "1 posting" in str(exc.value)
        assert uow.committed is False
        assert len(uow.accounts._accounts) == 1

    def test_delete_account_not_found_raises_error(self):
        uow = FakeUnitOfWork()
        with pytest.raises(AccountNotFoundError) as exc_info:
            delete_account(uow, account_id="nonexistent-id")

        assert "not found" in str(exc_info.value)
        assert "nonexistent-id" in str(exc_info.value)
        assert uow.committed is False

    def test_delete_account_with_outgoing_transfer_raises_error(self):
        uow = FakeUnitOfWork()
        source = create_account(
            uow,
            name="Source",
            currency="USD",
            initial_balance=Decimal(100),
        )
        dest = create_account(
            uow,
            name="Dest",
            currency="USD",
            initial_balance=Decimal(0),
        )
        create_transfer(
            uow,
            source_account_id=source.account_id,
            dest_account_id=dest.account_id,
            debit_amount=Decimal(50),
            credit_amount=Decimal(50),
            transfer_date=JAN_01,
        )
        uow.committed = False

        with pytest.raises(AccountHasTransfersError) as exc_info:
            delete_account(uow, account_id=source.account_id)

        assert "Cannot delete" in str(exc_info.value)
        assert "1 transfer" in str(exc_info.value)
        assert uow.committed is False
        assert len(uow.accounts._accounts) == 2

    def test_delete_account_with_incoming_transfer_raises_error(self):
        uow = FakeUnitOfWork()
        source = create_account(
            uow,
            name="Source",
            currency="USD",
            initial_balance=Decimal(100),
        )
        dest = create_account(
            uow,
            name="Dest",
            currency="USD",
            initial_balance=Decimal(0),
        )
        create_transfer(
            uow,
            source_account_id=source.account_id,
            dest_account_id=dest.account_id,
            debit_amount=Decimal(50),
            credit_amount=Decimal(50),
            transfer_date=JAN_01,
        )
        uow.committed = False

        with pytest.raises(AccountHasTransfersError) as exc_info:
            delete_account(uow, account_id=dest.account_id)

        assert "Cannot delete" in str(exc_info.value)
        assert uow.committed is False

    def test_delete_account_with_multiple_transfers_reports_count(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test",
            currency="USD",
            initial_balance=Decimal(100),
        )
        other1 = create_account(
            uow,
            name="Other1",
            currency="USD",
            initial_balance=Decimal(0),
        )
        other2 = create_account(
            uow,
            name="Other2",
            currency="USD",
            initial_balance=Decimal(100),
        )
        create_transfer(
            uow,
            source_account_id=account.account_id,
            dest_account_id=other1.account_id,
            debit_amount=Decimal(10),
            credit_amount=Decimal(10),
            transfer_date=JAN_01,
        )
        create_transfer(
            uow,
            source_account_id=other2.account_id,
            dest_account_id=account.account_id,
            debit_amount=Decimal(20),
            credit_amount=Decimal(20),
            transfer_date=JAN_01,
        )
        create_transfer(
            uow,
            source_account_id=account.account_id,
            dest_account_id=other2.account_id,
            debit_amount=Decimal(5),
            credit_amount=Decimal(5),
            transfer_date=JAN_01,
        )
        uow.committed = False

        with pytest.raises(AccountHasTransfersError) as exc_info:
            delete_account(uow, account_id=account.account_id)

        assert "3 transfer" in str(exc_info.value)

    def test_delete_account_with_postings_and_transfers_reports_both(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Combo",
            currency="USD",
            initial_balance=Decimal(100),
        )
        other = create_account(
            uow,
            name="Other",
            currency="USD",
            initial_balance=Decimal(0),
        )
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(10),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )
        create_transfer(
            uow,
            source_account_id=account.account_id,
            dest_account_id=other.account_id,
            debit_amount=Decimal(5),
            credit_amount=Decimal(5),
            transfer_date=JAN_01,
        )
        uow.committed = False

        with pytest.raises(AccountHasPostingsError) as exc_info:
            delete_account(uow, account_id=account.account_id)

        assert "posting" in str(exc_info.value)
        assert "transfer" in str(exc_info.value)
        assert uow.committed is False


class TestCreatePosting:
    def test_create_posting_success_expense(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        uow.committed = False

        posting = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(50),
            posting_date=date(2023, 1, 1),
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )

        assert posting.posting_id is not None
        assert posting.account_id == account.account_id
        assert posting.posting_date == date(2023, 1, 1)
        assert posting.category_id == category.category_id
        assert posting.posting_type == PostingType.EXPENSE
        assert posting.amount == Decimal("-50")
        assert account.balance == Decimal(50)
        postings = list_postings(uow, account_id=account.account_id)
        assert len(postings) == 1
        assert uow.committed is True

    def test_create_posting_success_income_no_category(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        posting = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(75),
            posting_date=date(2023, 1, 1),
            posting_type=PostingType.INCOME,
            category_id=None,
        )

        assert posting.posting_id is not None
        assert posting.account_id == account.account_id
        assert posting.category_id is None
        assert posting.posting_type == PostingType.INCOME
        assert posting.amount == Decimal("75")
        assert account.balance == Decimal(175)
        assert uow.committed is True

    def test_create_posting_account_not_found(self):
        uow = FakeUnitOfWork()
        with pytest.raises(
            AccountNotFoundError,
            match="Account with id 'non-existent-acc' not found",
        ):
            create_posting(
                uow,
                account_id="non-existent-acc",
                amount=Decimal(50),
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
            )

        assert uow.committed is False

    def test_create_posting_category_not_found(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        with pytest.raises(
            CategoryNotFoundError,
            match="Category with id 'non-existent-cat' not found",
        ):
            create_posting(
                uow,
                account_id=account.account_id,
                amount=Decimal(50),
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
                category_id="non-existent-cat",
            )

        assert uow.committed is False

    def test_create_posting_insufficient_funds(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(10),
        )
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        uow.committed = False

        with pytest.raises(
            InsufficientFundsError,
            match="Insufficient funds in account 'Test Account'",
        ):
            create_posting(
                uow,
                account_id=account.account_id,
                amount=Decimal(50),
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
                category_id=category.category_id,
            )

        assert uow.committed is False

    def test_create_posting_with_payee_and_description(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        uow.committed = False

        posting = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(50),
            posting_date=date(2023, 1, 1),
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
            payee="Restaurant XYZ",
            description="Team lunch",
        )

        assert posting.payee == "Restaurant XYZ"
        assert posting.description == "Team lunch"
        assert uow.committed is True


class TestGetPosting:
    def test_get_posting_success(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        created = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(50),
            posting_date=JAN_01,
            posting_type=PostingType.INCOME,
            category_id=None,
        )

        posting = get_posting(uow, posting_id=created.posting_id)

        assert posting == created
        assert posting.amount == Decimal(50)

    def test_get_posting_not_found_raises_error(self):
        uow = FakeUnitOfWork()
        with pytest.raises(PostingNotFoundError) as exc_info:
            get_posting(uow, posting_id="non-existent")

        assert "Posting with id 'non-existent' not found" in str(exc_info.value)


class TestListPostings:
    def test_list_postings_empty(self):
        uow = FakeUnitOfWork()
        postings = list_postings(uow)
        assert postings == []

    def test_list_postings_all(self):
        uow = FakeUnitOfWork()
        a1 = create_account(
            uow,
            name="A1",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        a2 = create_account(
            uow,
            name="A2",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        parent = create_category(uow, name="c1", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="c1-sub", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        create_posting(
            uow,
            account_id=a1.account_id,
            amount=Decimal(10),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )
        create_posting(
            uow,
            account_id=a2.account_id,
            amount=Decimal(20),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )

        postings = list_postings(uow)

        assert len(postings) == 2

    def test_list_postings_filtered_by_account(self):
        uow = FakeUnitOfWork()
        a1 = create_account(
            uow,
            name="A1",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        a2 = create_account(
            uow,
            name="A2",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        parent = create_category(uow, name="c1", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="c1-sub", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        p1 = create_posting(
            uow,
            account_id=a1.account_id,
            amount=Decimal(10),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )
        create_posting(
            uow,
            account_id=a2.account_id,
            amount=Decimal(20),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )

        postings = list_postings(uow, account_id=a1.account_id)

        assert len(postings) == 1
        assert postings[0] == p1


class TestDeletePosting:
    def test_delete_posting_success(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        posting = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(50),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )
        uow.committed = False

        delete_posting(uow, posting_id=posting.posting_id)

        assert uow.committed is True
        assert account.posting_count == 0
        postings = list_postings(uow, account_id=account.account_id)
        assert len(postings) == 0

    def test_delete_posting_not_found(self):
        uow = FakeUnitOfWork()
        with pytest.raises(PostingNotFoundError) as exc_info:
            delete_posting(uow, posting_id="nonexistent-id")

        assert "Posting with id 'nonexistent-id' not found" in str(exc_info.value)
        assert uow.committed is False

    def test_delete_posting_restores_balance(self):
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        category = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        posting = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(30),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )
        assert account.balance == Decimal(70)
        uow.committed = False

        delete_posting(uow, posting_id=posting.posting_id)

        assert account.balance == Decimal(100)
        assert uow.committed is True


class TestTransferServices:
    def test_create_transfer_success(self):
        uow = FakeUnitOfWork()
        source = create_account(
            uow,
            name="Source",
            currency="USD",
            initial_balance=Decimal(100),
        )
        dest = create_account(
            uow,
            name="Dest",
            currency="USD",
            initial_balance=Decimal(0),
        )
        uow.committed = False

        transfer = create_transfer(
            uow,
            source_account_id=source.account_id,
            dest_account_id=dest.account_id,
            debit_amount=Decimal(10),
            credit_amount=Decimal(10),
            transfer_date=JAN_01,
            description="Test Transfer",
        )

        assert transfer.source_account_id == source.account_id
        assert transfer.dest_account_id == dest.account_id
        assert transfer.debit_amount == Decimal(10)
        assert transfer.description == "Test Transfer"
        assert len(uow.transfers._transfers) == 1
        assert uow.committed is True

    def test_create_transfer_source_not_found(self):
        uow = FakeUnitOfWork()
        dest = create_account(
            uow,
            name="Dest",
            currency="USD",
            initial_balance=Decimal(0),
        )
        uow.committed = False

        with pytest.raises(AccountNotFoundError) as exc:
            create_transfer(
                uow,
                source_account_id="non-existent",
                dest_account_id=dest.account_id,
                debit_amount=Decimal(10),
                credit_amount=Decimal(10),
                transfer_date=JAN_01,
            )
        assert "Source account" in str(exc.value)

    def test_create_transfer_dest_not_found(self):
        uow = FakeUnitOfWork()
        source = create_account(
            uow,
            name="Source",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        with pytest.raises(AccountNotFoundError) as exc:
            create_transfer(
                uow,
                source_account_id=source.account_id,
                dest_account_id="non-existent",
                debit_amount=Decimal(10),
                credit_amount=Decimal(10),
                transfer_date=JAN_01,
            )
        assert "Destination account" in str(exc.value)

    def test_create_transfer_insufficient_funds(self):
        uow = FakeUnitOfWork()
        source = create_account(
            uow,
            name="Source",
            currency="USD",
            initial_balance=Decimal(5),
        )
        dest = create_account(
            uow,
            name="Dest",
            currency="USD",
            initial_balance=Decimal(0),
        )
        uow.committed = False

        with pytest.raises(InsufficientFundsError):
            create_transfer(
                uow,
                source_account_id=source.account_id,
                dest_account_id=dest.account_id,
                debit_amount=Decimal(10),
                credit_amount=Decimal(10),
                transfer_date=JAN_01,
            )

    def test_get_transfer_success(self):
        uow = FakeUnitOfWork()
        source = create_account(
            uow,
            name="Source",
            currency="USD",
            initial_balance=Decimal(100),
        )
        dest = create_account(
            uow,
            name="Dest",
            currency="USD",
            initial_balance=Decimal(0),
        )
        transfer = create_transfer(
            uow,
            source_account_id=source.account_id,
            dest_account_id=dest.account_id,
            debit_amount=Decimal(10),
            credit_amount=Decimal(10),
            transfer_date=JAN_01,
        )

        retrieved = get_transfer(uow, transfer_id=transfer.transfer_id)

        assert retrieved == transfer

    def test_get_transfer_not_found(self):
        uow = FakeUnitOfWork()
        with pytest.raises(TransferNotFoundError):
            get_transfer(uow, transfer_id="non-existent")

    def test_list_transfers(self):
        uow = FakeUnitOfWork()
        source = create_account(
            uow,
            name="Source",
            currency="USD",
            initial_balance=Decimal(100),
        )
        dest = create_account(
            uow,
            name="Dest",
            currency="USD",
            initial_balance=Decimal(0),
        )
        t1 = create_transfer(
            uow,
            source_account_id=source.account_id,
            dest_account_id=dest.account_id,
            debit_amount=Decimal(10),
            credit_amount=Decimal(10),
            transfer_date=JAN_01,
        )
        t2 = create_transfer(
            uow,
            source_account_id=source.account_id,
            dest_account_id=dest.account_id,
            debit_amount=Decimal(20),
            credit_amount=Decimal(20),
            transfer_date=JAN_01,
        )

        transfers = list_transfers(uow)

        assert len(transfers) == 2
        assert t1 in transfers
        assert t2 in transfers


class TestCategoryServices:
    def test_get_category_success(self):
        uow = FakeUnitOfWork()
        created = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)

        retrieved = get_category(uow, category_id=created.category_id)

        assert retrieved == created

    def test_get_category_not_found(self):
        uow = FakeUnitOfWork()
        with pytest.raises(CategoryNotFoundError):
            get_category(uow, category_id="non-existent")


class TestCategoryHierarchy:
    def test_create_parent_category(self):
        uow = FakeUnitOfWork()
        cat = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        assert cat.parent_id is None
        assert cat.category_type == CategoryType.EXPENSE

    def test_create_subcategory_success(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        child = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        assert child.parent_id == parent.category_id
        assert child.category_type == CategoryType.EXPENSE

    def test_create_subcategory_parent_not_found(self):
        uow = FakeUnitOfWork()
        with pytest.raises(CategoryNotFoundError):
            create_category(
                uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id="non-existent"
            )

    def test_create_subcategory_of_subcategory_raises_error(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        child = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        with pytest.raises(CategoryHierarchyError, match="max 2 levels"):
            create_category(
                uow,
                name="Organic",
                category_type=CategoryType.EXPENSE,
                parent_id=child.category_id,
            )

    def test_create_subcategory_type_mismatch_raises_error(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        with pytest.raises(CategoryHierarchyError, match="must match"):
            create_category(
                uow,
                name="Salary",
                category_type=CategoryType.INCOME,
                parent_id=parent.category_id,
            )

    def test_create_category_duplicate_name_same_parent(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        with pytest.raises(DuplicateCategoryNameError):
            create_category(
                uow,
                name="Groceries",
                category_type=CategoryType.EXPENSE,
                parent_id=parent.category_id,
            )

    def test_create_category_same_name_different_parents_succeeds(self):
        uow = FakeUnitOfWork()
        parent1 = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        parent2 = create_category(uow, name="Transport", category_type=CategoryType.EXPENSE)
        c1 = create_category(
            uow, name="Misc", category_type=CategoryType.EXPENSE, parent_id=parent1.category_id
        )
        c2 = create_category(
            uow, name="Misc", category_type=CategoryType.EXPENSE, parent_id=parent2.category_id
        )
        assert c1.name == c2.name
        assert c1.parent_id != c2.parent_id


class TestPostingCategoryEnforcement:
    def test_create_posting_with_parent_category_raises_error(self):
        uow = FakeUnitOfWork()
        account = create_account(uow, name="Test", currency="EUR", initial_balance=Decimal(100))
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        with pytest.raises(ParentCategoryPostingError, match="Use a subcategory"):
            create_posting(
                uow,
                account_id=account.account_id,
                amount=Decimal(10),
                posting_date=JAN_01,
                posting_type=PostingType.EXPENSE,
                category_id=parent.category_id,
            )

    def test_create_posting_with_subcategory_succeeds(self):
        uow = FakeUnitOfWork()
        account = create_account(uow, name="Test", currency="EUR", initial_balance=Decimal(100))
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        child = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        posting = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(10),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=child.category_id,
        )
        assert posting.category_id == child.category_id

    def test_create_posting_type_mismatch_raises_error(self):
        uow = FakeUnitOfWork()
        account = create_account(uow, name="Test", currency="EUR", initial_balance=Decimal(100))
        parent = create_category(uow, name="Salary", category_type=CategoryType.INCOME)
        child = create_category(
            uow, name="Monthly", category_type=CategoryType.INCOME, parent_id=parent.category_id
        )
        with pytest.raises(CategoryHierarchyError, match="does not match"):
            create_posting(
                uow,
                account_id=account.account_id,
                amount=Decimal(10),
                posting_date=JAN_01,
                posting_type=PostingType.EXPENSE,
                category_id=child.category_id,
            )


class TestDeleteCategoryHierarchy:
    def test_delete_parent_with_children_raises_error(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        with pytest.raises(CategoryHasChildrenError, match="has child categories"):
            delete_category(uow, category_id=parent.category_id)

    def test_delete_parent_without_children_succeeds(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        delete_category(uow, category_id=parent.category_id)
        assert len(uow.categories._categories) == 0


class TestListCategoryHierarchy:
    def test_list_parent_categories(self):
        uow = FakeUnitOfWork()
        p1 = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        p2 = create_category(uow, name="Income", category_type=CategoryType.INCOME)
        create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=p1.category_id
        )
        parents = list_parent_categories(uow)
        assert len(parents) == 2
        assert p1 in parents
        assert p2 in parents

    def test_list_subcategories(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        c1 = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        c2 = create_category(
            uow, name="Restaurant", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )
        children = list_subcategories(uow, parent_id=parent.category_id)
        assert len(children) == 2
        assert c1 in children
        assert c2 in children


class TestDeleteTransfer:
    def test_delete_transfer_success(self):
        uow = FakeUnitOfWork()
        acc1 = create_account(uow, name="Source", currency="EUR", initial_balance=Decimal(100))
        acc2 = create_account(uow, name="Dest", currency="EUR", initial_balance=Decimal(50))

        transfer = create_transfer(
            uow,
            source_account_id=acc1.account_id,
            dest_account_id=acc2.account_id,
            debit_amount=Decimal(30),
            credit_amount=Decimal(30),
            transfer_date=JAN_01,
        )

        assert acc1.balance == Decimal(70)
        assert acc2.balance == Decimal(80)
        uow.committed = False

        delete_transfer(uow, transfer_id=transfer.transfer_id)

        assert uow.committed is True
        assert acc1.balance == Decimal(100)
        assert acc2.balance == Decimal(50)
        assert len(uow.transfers._transfers) == 0

    def test_delete_transfer_not_found(self):
        uow = FakeUnitOfWork()
        with pytest.raises(TransferNotFoundError) as exc_info:
            delete_transfer(uow, transfer_id="nonexistent")
        assert "Transfer with id 'nonexistent' not found" in str(exc_info.value)
        assert uow.committed is False
