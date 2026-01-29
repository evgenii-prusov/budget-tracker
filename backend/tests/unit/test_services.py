import pytest
from decimal import Decimal
from datetime import date

from app.domain.model import Account
from app.domain.model import Transfer
from app.domain.model import Posting
from app.domain.model import PostingType
from app.domain.model import Category
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import InsufficientFundsError
from app.domain.exceptions import PostingNotFoundError
from app.domain.exceptions import TransferNotFoundError

from app.service_layer.abstract_repository import AbstractRepository
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.service_layer.services import create_account
from app.service_layer.services import delete_account
from app.service_layer.services import create_category
from app.service_layer.services import create_posting
from app.service_layer.services import get_posting
from app.service_layer.services import list_postings
from app.service_layer.services import update_account_name
from app.service_layer.services import create_transfer
from app.service_layer.services import get_transfer
from app.service_layer.services import list_transfers
from tests.constants import JAN_01


class FakeRepository(AbstractRepository):
    def __init__(self, accounts: list[Account] | None = None):
        self.accounts = accounts or []
        self.transfers: list[Transfer] = []
        self.categories: list[Category] = []

    def add(self, account: Account):
        self.accounts.append(account)

    def get(self, account_id: str) -> Account | None:
        try:
            account = next(acc for acc in self.accounts if acc.account_id == account_id)
        except StopIteration:
            return None
        return account

    def get_by_name(self, name: str) -> Account | None:
        return next((acc for acc in self.accounts if acc.name == name), None)

    def list_all(self) -> list[Account]:
        return list(self.accounts)

    def add_transfer(self, transfer: Transfer):
        self.transfers.append(transfer)

    def get_transfer(self, transfer_id: str) -> Transfer | None:
        return next(
            (t for t in self.transfers if t.transfer_id == transfer_id),
            None,
        )

    def list_transfers_for_account(self, account_id: str) -> list[Transfer]:
        return [
            t
            for t in self.transfers
            if t.source_account_id == account_id or t.dest_account_id == account_id
        ]

    def list_transfers(self) -> list[Transfer]:
        return list(self.transfers)

    def delete(self, account: Account) -> None:
        self.accounts.remove(account)

    def add_category(self, category: Category):
        self.categories.append(category)

    def get_category(self, category_id: str) -> Category | None:
        return next(
            (c for c in self.categories if c.category_id == category_id),
            None,
        )

    def get_category_by_name(self, name: str) -> Category | None:
        return next((c for c in self.categories if c.name == name), None)

    def list_categories(self) -> list[Category]:
        return list(self.categories)

    def delete_category(self, category: Category) -> None:
        self.categories.remove(category)

    def count_postings_for_category(self, category_id: str) -> int:
        count = 0
        for acc in self.accounts:
            for p in acc._postings:
                if p.category_id == category_id:
                    count += 1
        return count

    def get_posting(self, posting_id: str) -> Posting | None:
        for acc in self.accounts:
            for p in acc._postings:
                if p.posting_id == posting_id:
                    return p
        return None

    def list_postings(self, account_id: str | None = None) -> list[Posting]:
        all_postings = []
        for acc in self.accounts:
            if account_id is None or acc.account_id == account_id:
                all_postings.extend(acc._postings)
        return all_postings


class FakeUnitOfWork(AbstractUnitOfWork):
    repo: FakeRepository

    def __init__(self, accounts: list[Account] | None = None):
        self.repo = FakeRepository(accounts)
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


class TestCreateAccount:
    def test_create_account_success(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act
        account = create_account(
            uow,
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
        )

        # Assert
        assert account.name == "Test Account"
        assert account.currency == "USD"
        assert account.initial_balance == Decimal(100)
        assert uow.committed is True
        assert len(uow.repo.accounts) == 1

    def test_create_account_with_zero_balance(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act
        account = create_account(
            uow,
            name="Zero Balance",
            currency="EUR",
            initial_balance=Decimal(0),
        )

        # Assert
        assert account.initial_balance == Decimal(0)
        assert uow.committed is True

    def test_create_account_duplicate_name_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()
        create_account(
            uow,
            name="Existing Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        # Act & Assert
        with pytest.raises(DuplicateAccountNameError) as exc_info:
            create_account(
                uow,
                name="Existing Account",
                currency="EUR",
                initial_balance=Decimal(0),
            )

        assert "already exists" in str(exc_info.value)
        assert "Existing Account" in str(exc_info.value)
        assert uow.committed is False  # Should not commit on error

    def test_create_account_negative_balance_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
        with pytest.raises(
            InvalidInitialBalanceError,
        ) as exc_info:
            create_account(
                uow,
                name="Negative Account",
                currency="USD",
                initial_balance=Decimal(-100),
            )

        assert "cannot be negative" in str(exc_info.value)
        assert "-100" in str(exc_info.value)
        assert uow.committed is False  # Should not commit on error
        assert len(uow.repo.accounts) == 0  # Should not add account


class TestUpdateAccountName:
    def test_update_account_name_success(self):
        # Arrange
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Old Name",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        # Act
        updated_account = update_account_name(
            uow,
            account_id=account.account_id,
            new_name="New Name",
        )

        # Assert
        assert updated_account.name == "New Name"
        assert uow.committed is True

    def test_update_account_name_duplicate_name_raises_error(self):
        # Arrange
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

        # Act & Assert
        with pytest.raises(DuplicateAccountNameError) as exc_info:
            update_account_name(
                uow,
                account_id=account1.account_id,
                new_name="Account 2",
            )

        assert "already exists" in str(exc_info.value)
        assert uow.committed is False
        assert account1.name == "Account 1"  # Should not change name

    def test_update_account_name_not_found_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc_info:
            update_account_name(
                uow,
                account_id="nonexistent-id",
                new_name="New Name",
            )

        assert "not found" in str(exc_info.value)
        assert uow.committed is False


class TestDeleteAccount:
    def test_delete_account_success(self):
        # Arrange
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        # Act
        delete_account(uow, account_id=account.account_id)

        # Assert
        assert uow.committed is True
        assert len(uow.repo.accounts) == 0

    def test_delete_account_with_postings_succeeds(self):
        """Service allows deletion when account has postings (cascade is ORM concern)."""
        # Arrange
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        category = create_category(uow, name="Food")
        create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(100),
            posting_date=JAN_01,
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )
        uow.committed = False

        # Act
        delete_account(uow, account_id=account.account_id)

        # Assert
        assert uow.committed is True
        assert len(uow.repo.accounts) == 0

    def test_delete_account_not_found_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc_info:
            delete_account(uow, account_id="nonexistent-id")

        assert "not found" in str(exc_info.value)
        assert "nonexistent-id" in str(exc_info.value)
        assert uow.committed is False

    def test_delete_account_with_outgoing_transfer_raises_error(
        self,
    ):
        # Arrange
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

        # Act & Assert
        with pytest.raises(
            AccountHasTransfersError,
        ) as exc_info:
            delete_account(uow, account_id=source.account_id)

        assert "Cannot delete" in str(exc_info.value)
        assert "1 transfer" in str(exc_info.value)
        assert uow.committed is False
        assert len(uow.repo.accounts) == 2  # Account not removed

    def test_delete_account_with_incoming_transfer_raises_error(
        self,
    ):
        # Arrange
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

        # Act & Assert
        with pytest.raises(
            AccountHasTransfersError,
        ) as exc_info:
            delete_account(uow, account_id=dest.account_id)

        assert "Cannot delete" in str(exc_info.value)
        assert uow.committed is False

    def test_delete_account_with_multiple_transfers_reports_count(
        self,
    ):
        # Arrange
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

        # Act & Assert
        with pytest.raises(
            AccountHasTransfersError,
        ) as exc_info:
            delete_account(uow, account_id=account.account_id)

        assert "3 transfer" in str(exc_info.value)


class TestCreatePosting:
    def test_create_posting_success_expense(self):
        # Arrange
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        category = create_category(uow, name="Food")
        uow.committed = False

        # Act
        posting = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(50),
            posting_date=date(2023, 1, 1),
            posting_type=PostingType.EXPENSE,
            category_id=category.category_id,
        )

        # Assert
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
        # Arrange
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        # Act
        posting = create_posting(
            uow,
            account_id=account.account_id,
            amount=Decimal(75),
            posting_date=date(2023, 1, 1),
            posting_type=PostingType.INCOME,
            category_id=None,
        )

        # Assert
        assert posting.posting_id is not None
        assert posting.account_id == account.account_id
        assert posting.category_id is None
        assert posting.posting_type == PostingType.INCOME
        assert posting.amount == Decimal("75")
        assert account.balance == Decimal(175)
        assert uow.committed is True

    def test_create_posting_account_not_found(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
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
        # Arrange
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        # Act & Assert
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
        # Arrange
        uow = FakeUnitOfWork()
        account = create_account(
            uow,
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(10),
        )
        category = create_category(uow, name="Food")
        uow.committed = False

        # Act & Assert
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


class TestGetPosting:
    def test_get_posting_success(self):
        # Arrange
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

        # Act
        posting = get_posting(uow, posting_id=created.posting_id)

        # Assert
        assert posting == created
        assert posting.amount == Decimal(50)

    def test_get_posting_not_found_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
        with pytest.raises(PostingNotFoundError) as exc_info:
            get_posting(uow, posting_id="non-existent")

        assert "Posting with id 'non-existent' not found" in str(exc_info.value)


class TestListPostings:
    def test_list_postings_empty(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act
        postings = list_postings(uow)

        # Assert
        assert postings == []

    def test_list_postings_all(self):
        # Arrange
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
        category = create_category(uow, name="c1")
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

        # Act
        postings = list_postings(uow)

        # Assert
        assert len(postings) == 2

    def test_list_postings_filtered_by_account(self):
        # Arrange
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
        category = create_category(uow, name="c1")
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

        # Act
        postings = list_postings(uow, account_id=a1.account_id)

        # Assert
        assert len(postings) == 1
        assert postings[0] == p1


class TestTransferServices:
    def test_create_transfer_success(self):
        # Arrange
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

        # Act
        transfer = create_transfer(
            uow,
            source_account_id=source.account_id,
            dest_account_id=dest.account_id,
            debit_amount=Decimal(10),
            credit_amount=Decimal(10),
            transfer_date=JAN_01,
            description="Test Transfer",
        )

        # Assert
        assert transfer.source_account_id == source.account_id
        assert transfer.dest_account_id == dest.account_id
        assert transfer.debit_amount == Decimal(10)
        assert transfer.description == "Test Transfer"
        assert len(uow.repo.transfers) == 1
        assert uow.committed is True

    def test_create_transfer_source_not_found(self):
        # Arrange
        uow = FakeUnitOfWork()
        dest = create_account(
            uow,
            name="Dest",
            currency="USD",
            initial_balance=Decimal(0),
        )
        uow.committed = False

        # Act & Assert
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
        # Arrange
        uow = FakeUnitOfWork()
        source = create_account(
            uow,
            name="Source",
            currency="USD",
            initial_balance=Decimal(100),
        )
        uow.committed = False

        # Act & Assert
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
        # Arrange
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

        # Act & Assert
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
        # Arrange
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

        # Act
        retrieved = get_transfer(uow, transfer_id=transfer.transfer_id)

        # Assert
        assert retrieved == transfer

    def test_get_transfer_not_found(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
        with pytest.raises(TransferNotFoundError):
            get_transfer(uow, transfer_id="non-existent")

    def test_list_transfers(self):
        # Arrange
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

        # Act
        transfers = list_transfers(uow)

        # Assert
        assert len(transfers) == 2
        assert t1 in transfers
        assert t2 in transfers
