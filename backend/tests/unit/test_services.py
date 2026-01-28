import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock

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

from app.service_layer.abstract_repository import AbstractRepository
from app.service_layer.services import create_account
from app.service_layer.services import delete_account
from app.service_layer.services import create_posting  # Import create_posting
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

    def get_transfer(self, transfer_id: str) -> Transfer:
        return next(t for t in self.transfers if t.transfer_id == transfer_id)

    def list_transfers_for_account(self, account_id: str) -> list[Transfer]:
        return [
            t
            for t in self.transfers
            if t.source_account_id == account_id or t.dest_account_id == account_id
        ]

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


# Unit tests for create_posting service
class TestCreatePosting:
    def test_create_posting_success_expense(self):
        mock_repo = Mock(spec=AbstractRepository)

        # Use a real Account instance for testing its domain logic
        real_account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        mock_repo.get.return_value = real_account

        # Mock category retrieval
        mock_category_id = "cat-1"
        mock_category = Mock()  # A mock category object is enough
        mock_repo.get_category.return_value = mock_category

        posting_date = date(2023, 1, 1)
        amount = Decimal(50)
        posting_type = PostingType.EXPENSE

        # Call the service function
        created_posting = create_posting(
            mock_repo,
            account_id="acc-1",
            amount=amount,
            posting_date=posting_date,
            posting_type=posting_type,
            category_id=mock_category_id,
        )

        # Assertions
        mock_repo.get.assert_called_once_with("acc-1")
        mock_repo.get_category.assert_called_once_with(mock_category_id)
        mock_repo.commit.assert_called_once()

        # Verify the returned posting object
        assert isinstance(created_posting, Posting)
        assert created_posting.account_id == "acc-1"
        assert created_posting.posting_date == posting_date
        assert created_posting.category_id == mock_category_id
        assert created_posting.posting_type == PostingType.EXPENSE

        # The amount should be signed by Account.record_posting (negative for EXPENSE)
        assert created_posting.amount == Decimal("-50")

        # Check that the posting was added to the real account instance's postings
        assert len(real_account._postings) == 1
        assert real_account._postings[0] == created_posting
        assert real_account.balance == Decimal(100) - Decimal(
            50
        )  # Check account balance update

    def test_create_posting_success_income_no_category(self):
        mock_repo = Mock(spec=AbstractRepository)
        real_account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        mock_repo.get.return_value = real_account

        posting_date = date(2023, 1, 1)
        amount = Decimal(75)
        posting_type = PostingType.INCOME

        created_posting = create_posting(
            mock_repo,
            account_id="acc-1",
            amount=amount,
            posting_date=posting_date,
            posting_type=posting_type,
            category_id=None,
        )

        mock_repo.get.assert_called_once_with("acc-1")
        mock_repo.get_category.assert_not_called()  # Category not used
        mock_repo.commit.assert_called_once()

        assert isinstance(created_posting, Posting)
        assert created_posting.account_id == "acc-1"
        assert created_posting.posting_date == posting_date
        assert created_posting.category_id is None
        assert created_posting.posting_type == PostingType.INCOME
        assert created_posting.amount == Decimal(
            "75"
        )  # For INCOME, amount should be positive

        assert len(real_account._postings) == 1
        assert real_account._postings[0] == created_posting
        assert real_account.balance == Decimal(100) + Decimal(75)

    def test_create_posting_account_not_found(self):
        mock_repo = Mock(spec=AbstractRepository)
        mock_repo.get.return_value = None  # Account not found

        with pytest.raises(
            AccountNotFoundError, match="Account with id 'non-existent-acc' not found"
        ):
            create_posting(
                mock_repo,
                account_id="non-existent-acc",
                amount=Decimal(50),
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
            )

        mock_repo.get.assert_called_once_with("non-existent-acc")
        mock_repo.get_category.assert_not_called()
        mock_repo.commit.assert_not_called()

    def test_create_posting_category_not_found(self):
        mock_repo = Mock(spec=AbstractRepository)
        real_account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(100),
        )
        mock_repo.get.return_value = real_account
        mock_repo.get_category.return_value = None  # Category not found

        with pytest.raises(
            CategoryNotFoundError, match="Category with id 'non-existent-cat' not found"
        ):
            create_posting(
                mock_repo,
                account_id="acc-1",
                amount=Decimal(50),
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
                category_id="non-existent-cat",
            )

        mock_repo.get.assert_called_once_with("acc-1")
        mock_repo.get_category.assert_called_once_with("non-existent-cat")
        mock_repo.commit.assert_not_called()

    def test_create_posting_insufficient_funds(self):
        mock_repo = Mock(spec=AbstractRepository)
        real_account = Account(
            account_id="acc-1",
            name="Test Account",
            currency="EUR",
            initial_balance=Decimal(10),  # Low balance
        )
        mock_repo.get.return_value = real_account

        # Mock category retrieval, as it's called before InsufficientFundsError is raised
        # from Account.record_posting
        mock_repo.get_category.return_value = Mock()

        # When services.create_posting calls real_account.record_posting,
        # it should raise InsufficientFundsError because the balance is too low.
        with pytest.raises(
            InsufficientFundsError, match="Insufficient funds in account 'Test Account'"
        ):
            create_posting(
                mock_repo,
                account_id="acc-1",
                amount=Decimal(50),  # Amount larger than balance
                posting_date=date(2023, 1, 1),
                posting_type=PostingType.EXPENSE,
                category_id="cat-1",
            )

        mock_repo.get.assert_called_once_with("acc-1")
        mock_repo.get_category.assert_called_once_with(
            "cat-1"
        )  # Category lookup happens first
        mock_repo.commit.assert_not_called()  # Commit should not happen on error
