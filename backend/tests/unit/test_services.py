import pytest
from decimal import Decimal
from datetime import date

from app.domain.model import Account
from app.domain.model import Transfer
from app.domain.model import PostingType
from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError

from app.service_layer.abstract_repository import AbstractRepository
from app.service_layer.services import create_account
from app.service_layer.services import delete_account


class FakeRepository(AbstractRepository):
    def __init__(self, accounts: list[Account] | None = None):
        self.accounts = accounts or []
        self.transfers: list[Transfer] = []
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
            Decimal(50),
            date(2025, 1, 1),
            category="food",
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
