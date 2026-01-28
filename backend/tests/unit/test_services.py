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
from app.service_layer.services import create_account
from app.service_layer.services import delete_account
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
        self.committed = False

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

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False

    def add_transfer(self, transfer: Transfer):
        self.transfers.append(transfer)

    def get_transfer(self, transfer_id: str) -> Transfer | None:
        return next((t for t in self.transfers if t.transfer_id == transfer_id), None)

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
        return next((c for c in self.categories if c.category_id == category_id), None)

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


class TestCreateAccount:
    def test_create_account_success(self):
        # Arrange
        repo = FakeRepository()

        # Act
        account = create_account(
            repo, name="Test Account", currency="USD", initial_balance=Decimal(100)
        )

        # Assert
        assert account.name == "Test Account"
        assert account.currency == "USD"
        assert account.initial_balance == Decimal(100)
        assert repo.committed is True
        assert len(repo.accounts) == 1

    def test_create_account_with_zero_balance(self):
        # Arrange
        repo = FakeRepository()

        # Act
        account = create_account(
            repo,
            name="Zero Balance",
            currency="EUR",
            initial_balance=Decimal(0),
        )

        # Assert
        assert account.initial_balance == Decimal(0)
        assert repo.committed is True

    def test_create_account_duplicate_name_raises_error(self):
        # Arrange
        existing = Account(
            account_id="existing-id",
            name="Existing Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        repo = FakeRepository(accounts=[existing])

        # Act & Assert
        with pytest.raises(DuplicateAccountNameError) as exc_info:
            create_account(
                repo,
                name="Existing Account",
                currency="EUR",
                initial_balance=Decimal(0),
            )

        assert "already exists" in str(exc_info.value)
        assert "Existing Account" in str(exc_info.value)
        assert repo.committed is False  # Should not commit on error

    def test_create_account_negative_balance_raises_error(self):
        # Arrange
        repo = FakeRepository()

        # Act & Assert
        with pytest.raises(InvalidInitialBalanceError) as exc_info:
            create_account(
                repo,
                name="Negative Account",
                currency="USD",
                initial_balance=Decimal(-100),
            )

        assert "cannot be negative" in str(exc_info.value)
        assert "-100" in str(exc_info.value)
        assert repo.committed is False  # Should not commit on error
        assert len(repo.accounts) == 0  # Should not add account


class TestUpdateAccountName:
    def test_update_account_name_success(self):
        # Arrange
        account = Account(
            account_id="acc-1",
            name="Old Name",
            currency="USD",
            initial_balance=Decimal(100),
        )
        repo = FakeRepository(accounts=[account])

        # Act
        updated_account = update_account_name(
            repo, account_id="acc-1", new_name="New Name"
        )

        # Assert
        assert updated_account.name == "New Name"
        assert repo.committed is True

    def test_update_account_name_duplicate_name_raises_error(self):
        # Arrange
        account1 = Account(
            account_id="acc-1",
            name="Account 1",
            currency="USD",
            initial_balance=Decimal(100),
        )
        account2 = Account(
            account_id="acc-2",
            name="Account 2",
            currency="USD",
            initial_balance=Decimal(100),
        )
        repo = FakeRepository(accounts=[account1, account2])

        # Act & Assert
        with pytest.raises(DuplicateAccountNameError) as exc_info:
            update_account_name(repo, account_id="acc-1", new_name="Account 2")

        assert "already exists" in str(exc_info.value)
        assert repo.committed is False
        assert account1.name == "Account 1"  # Should not change name

    def test_update_account_name_not_found_raises_error(self):
        # Arrange
        repo = FakeRepository()

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc_info:
            update_account_name(repo, account_id="nonexistent-id", new_name="New Name")

        assert "not found" in str(exc_info.value)
        assert repo.committed is False


class TestDeleteAccount:
    def test_delete_account_success(self):
        # Arrange
        account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        repo = FakeRepository(accounts=[account])

        # Act
        delete_account(repo, account_id="acc-1")

        # Assert
        assert repo.committed is True
        assert len(repo.accounts) == 0

    def test_delete_account_with_postings_succeeds(self):
        """Service allows deletion when account has postings (cascade is ORM concern)."""
        # Arrange
        account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        account.record_posting(
            amount=Decimal("100.00"),
            posting_date=JAN_01,
            category_id="FOOD",
            posting_type=PostingType.EXPENSE,
        )
        repo = FakeRepository(accounts=[account])

        # Act
        delete_account(repo, account_id="acc-1")

        # Assert
        assert repo.committed is True
        assert len(repo.accounts) == 0

    def test_delete_account_not_found_raises_error(self):
        # Arrange
        repo = FakeRepository()

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc_info:
            delete_account(repo, account_id="nonexistent-id")

        assert "not found" in str(exc_info.value)
        assert "nonexistent-id" in str(exc_info.value)
        assert repo.committed is False

    def test_delete_account_with_outgoing_transfer_raises_error(self):
        # Arrange
        source = Account("acc-1", "Source", "USD", Decimal(100))
        dest = Account("acc-2", "Dest", "USD", Decimal(0))
        transfer = Transfer(
            transfer_id="t-1",
            source_account_id="acc-1",
            dest_account_id="acc-2",
            debit_amount=Decimal(50),
            credit_amount=Decimal(50),
            transfer_date=date(2025, 1, 1),
        )
        repo = FakeRepository(accounts=[source, dest])
        repo.transfers = [transfer]

        # Act & Assert
        with pytest.raises(AccountHasTransfersError) as exc_info:
            delete_account(repo, account_id="acc-1")

        assert "Cannot delete" in str(exc_info.value)
        assert "1 transfer" in str(exc_info.value)
        assert repo.committed is False
        assert len(repo.accounts) == 2  # Account not removed

    def test_delete_account_with_incoming_transfer_raises_error(self):
        # Arrange
        source = Account("acc-1", "Source", "USD", Decimal(100))
        dest = Account("acc-2", "Dest", "USD", Decimal(0))
        transfer = Transfer(
            transfer_id="t-1",
            source_account_id="acc-1",
            dest_account_id="acc-2",
            debit_amount=Decimal(50),
            credit_amount=Decimal(50),
            transfer_date=date(2025, 1, 1),
        )
        repo = FakeRepository(accounts=[source, dest])
        repo.transfers = [transfer]

        # Act & Assert
        with pytest.raises(AccountHasTransfersError) as exc_info:
            delete_account(repo, account_id="acc-2")

        assert "Cannot delete" in str(exc_info.value)
        assert repo.committed is False

    def test_delete_account_with_multiple_transfers_reports_count(self):
        # Arrange
        account = Account("acc-1", "Test", "USD", Decimal(100))
        other1 = Account("acc-2", "Other1", "USD", Decimal(0))
        other2 = Account("acc-3", "Other2", "USD", Decimal(0))
        transfers = [
            Transfer(
                "t-1",
                "acc-1",
                "acc-2",
                Decimal(10),
                Decimal(10),
                date(2025, 1, 1),
            ),
            Transfer(
                "t-2",
                "acc-3",
                "acc-1",
                Decimal(20),
                Decimal(20),
                date(2025, 1, 2),
            ),
            Transfer(
                "t-3",
                "acc-1",
                "acc-3",
                Decimal(5),
                Decimal(5),
                date(2025, 1, 3),
            ),
        ]
        repo = FakeRepository(accounts=[account, other1, other2])
        repo.transfers = transfers

        # Act & Assert
        with pytest.raises(AccountHasTransfersError) as exc_info:
            delete_account(repo, account_id="acc-1")

        assert "3 transfer" in str(exc_info.value)


class TestCreatePosting:
    def test_create_posting_success_expense(self):
        # Arrange
        account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        category = Category(category_id="cat-1", name="Food")
        repo = FakeRepository(accounts=[account])
        repo.add_category(category)

        # Act
        posting = create_posting(
            repo,
            account_id="acc-1",
            amount=Decimal(50),
            posting_date=date(2023, 1, 1),
            posting_type=PostingType.EXPENSE,
            category_id="cat-1",
        )

        # Assert
        assert isinstance(posting, Posting)
        assert posting.account_id == "acc-1"
        assert posting.posting_date == date(2023, 1, 1)
        assert posting.category_id == "cat-1"
        assert posting.posting_type == PostingType.EXPENSE
        assert posting.amount == Decimal("-50")  # Negative for expense
        assert account.balance == Decimal(50)  # 100 - 50
        assert len(account._postings) == 1
        assert repo.committed is True

    def test_create_posting_success_income_no_category(self):
        # Arrange
        account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        repo = FakeRepository(accounts=[account])

        # Act
        posting = create_posting(
            repo,
            account_id="acc-1",
            amount=Decimal(75),
            posting_date=date(2023, 1, 1),
            posting_type=PostingType.INCOME,
            category_id=None,
        )

        # Assert
        assert isinstance(posting, Posting)
        assert posting.account_id == "acc-1"
        assert posting.category_id is None
        assert posting.posting_type == PostingType.INCOME
        assert posting.amount == Decimal("75")  # Positive for income
        assert account.balance == Decimal(175)  # 100 + 75
        assert repo.committed is True

    def test_create_posting_account_not_found(self):
        # Arrange
        repo = FakeRepository()

        # Act & Assert
        with pytest.raises(
            AccountNotFoundError, match="Account with id 'non-existent-acc' not found"
        ):
            create_posting(
                repo,
                account_id="non-existent-acc",
                amount=Decimal(50),
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
            )

        assert repo.committed is False

    def test_create_posting_category_not_found(self):
        # Arrange
        account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        repo = FakeRepository(accounts=[account])

        # Act & Assert
        with pytest.raises(
            CategoryNotFoundError, match="Category with id 'non-existent-cat' not found"
        ):
            create_posting(
                repo,
                account_id="acc-1",
                amount=Decimal(50),
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
                category_id="non-existent-cat",
            )

        assert repo.committed is False

    def test_create_posting_insufficient_funds(self):
        # Arrange
        account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(10),  # Low balance
        )
        category = Category(category_id="cat-1", name="Food")
        repo = FakeRepository(accounts=[account])
        repo.add_category(category)

        # Act & Assert
        with pytest.raises(
            InsufficientFundsError, match="Insufficient funds in account 'Test Account'"
        ):
            create_posting(
                repo,
                account_id="acc-1",
                amount=Decimal(50),  # Amount larger than balance
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
                category_id="cat-1",
            )

        assert repo.committed is False


class TestGetPosting:
    def test_get_posting_success(self):
        # Arrange
        account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        account.record_posting(
            amount=Decimal(50),
            posting_date=JAN_01,
            category_id="cat-1",
            posting_type=PostingType.INCOME,
        )
        repo = FakeRepository(accounts=[account])
        posting_id = account._postings[0].posting_id

        # Act
        posting = get_posting(repo, posting_id=posting_id)

        # Assert
        assert posting == account._postings[0]
        assert posting.amount == Decimal(50)

    def test_get_posting_not_found_raises_error(self):
        # Arrange
        repo = FakeRepository()

        # Act & Assert
        with pytest.raises(PostingNotFoundError) as exc_info:
            get_posting(repo, posting_id="non-existent")

        assert "Posting with id 'non-existent' not found" in str(exc_info.value)


class TestListPostings:
    def test_list_postings_empty(self):
        # Arrange
        repo = FakeRepository()

        # Act
        postings = list_postings(repo)

        # Assert
        assert postings == []

    def test_list_postings_all(self):
        # Arrange
        a1 = Account("a1", "A1", "EUR", Decimal(100))
        a2 = Account("a2", "A2", "EUR", Decimal(100))
        a1.record_posting(
            Decimal(10), JAN_01, category_id="c1", posting_type=PostingType.EXPENSE
        )
        a2.record_posting(
            Decimal(20), JAN_01, category_id="c1", posting_type=PostingType.EXPENSE
        )
        repo = FakeRepository(accounts=[a1, a2])

        # Act
        postings = list_postings(repo)

        # Assert
        assert len(postings) == 2

    def test_list_postings_filtered_by_account(self):
        # Arrange
        a1 = Account("a1", "A1", "EUR", Decimal(100))
        a2 = Account("a2", "A2", "EUR", Decimal(100))
        p1 = a1.record_posting(
            Decimal(10), JAN_01, category_id="c1", posting_type=PostingType.EXPENSE
        )
        _p2 = a2.record_posting(
            Decimal(20), JAN_01, category_id="c1", posting_type=PostingType.EXPENSE
        )
        repo = FakeRepository(accounts=[a1, a2])

        # Act
        postings = list_postings(repo, account_id="a1")

        # Assert
        assert len(postings) == 1
        assert postings[0] == p1


class TestTransferServices:
    def test_create_transfer_success(self):
        # Arrange
        source = Account("src", "Source", "USD", Decimal(100))
        dest = Account("dst", "Dest", "USD", Decimal(0))
        repo = FakeRepository(accounts=[source, dest])

        # Act
        transfer = create_transfer(
            repo,
            source_account_id="src",
            dest_account_id="dst",
            debit_amount=Decimal(10),
            credit_amount=Decimal(10),
            transfer_date=JAN_01,
            description="Test Transfer",
        )

        # Assert
        assert transfer.source_account_id == "src"
        assert transfer.dest_account_id == "dst"
        assert transfer.debit_amount == Decimal(10)
        assert transfer.description == "Test Transfer"
        assert len(repo.transfers) == 1
        assert repo.committed is True

    def test_create_transfer_source_not_found(self):
        # Arrange
        dest = Account("dst", "Dest", "USD", Decimal(0))
        repo = FakeRepository(accounts=[dest])

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc:
            create_transfer(
                repo,
                source_account_id="src",
                dest_account_id="dst",
                debit_amount=Decimal(10),
                credit_amount=Decimal(10),
                transfer_date=JAN_01,
            )
        assert "Source account" in str(exc.value)

    def test_create_transfer_dest_not_found(self):
        # Arrange
        source = Account("src", "Source", "USD", Decimal(100))
        repo = FakeRepository(accounts=[source])

        # Act & Assert
        with pytest.raises(AccountNotFoundError) as exc:
            create_transfer(
                repo,
                source_account_id="src",
                dest_account_id="dst",
                debit_amount=Decimal(10),
                credit_amount=Decimal(10),
                transfer_date=JAN_01,
            )
        assert "Destination account" in str(exc.value)

    def test_create_transfer_insufficient_funds(self):
        # Arrange
        source = Account("src", "Source", "USD", Decimal(5))
        dest = Account("dst", "Dest", "USD", Decimal(0))
        repo = FakeRepository(accounts=[source, dest])

        # Act & Assert
        with pytest.raises(InsufficientFundsError):
            create_transfer(
                repo,
                source_account_id="src",
                dest_account_id="dst",
                debit_amount=Decimal(10),
                credit_amount=Decimal(10),
                transfer_date=JAN_01,
            )

    def test_get_transfer_success(self):
        # Arrange
        source = Account("src", "Source", "USD", Decimal(100))
        dest = Account("dst", "Dest", "USD", Decimal(0))
        repo = FakeRepository(accounts=[source, dest])
        transfer = create_transfer(
            repo,
            source_account_id="src",
            dest_account_id="dst",
            debit_amount=Decimal(10),
            credit_amount=Decimal(10),
            transfer_date=JAN_01,
        )

        # Act
        retrieved = get_transfer(repo, transfer_id=transfer.transfer_id)

        # Assert
        assert retrieved == transfer

    def test_get_transfer_not_found(self):
        # Arrange
        repo = FakeRepository()

        # Act & Assert
        with pytest.raises(TransferNotFoundError):
            get_transfer(repo, transfer_id="non-existent")

    def test_list_transfers(self):
        # Arrange
        source = Account("src", "Source", "USD", Decimal(100))
        dest = Account("dst", "Dest", "USD", Decimal(0))
        repo = FakeRepository(accounts=[source, dest])
        t1 = create_transfer(
            repo,
            source_account_id="src",
            dest_account_id="dst",
            debit_amount=Decimal(10),
            credit_amount=Decimal(10),
            transfer_date=JAN_01,
        )
        t2 = create_transfer(
            repo,
            source_account_id="src",
            dest_account_id="dst",
            debit_amount=Decimal(20),
            credit_amount=Decimal(20),
            transfer_date=JAN_01,
        )

        # Act
        transfers = list_transfers(repo)

        # Assert
        assert len(transfers) == 2
        assert t1 in transfers
        assert t2 in transfers
