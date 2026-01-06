import pytest
from decimal import Decimal

from app.model import (
    Account,
    DuplicateAccountNameError,
    InvalidInitialBalanceError,
)
from app.repository import AbstractRepository
from app.services import create_account


class FakeRepository(AbstractRepository):
    def __init__(self, accounts: list[Account] | None = None):
        self.accounts = accounts or []
        self.committed = False

    def add(self, account: Account):
        self.accounts.append(account)

    def get(self, account_id: str) -> Account:
        return next(acc for acc in self.accounts if acc.id == account_id)

    def get_by_name(self, name: str) -> Account | None:
        return next((acc for acc in self.accounts if acc.name == name), None)

    def list_all(self) -> list[Account]:
        return list(self.accounts)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False


class TestCreateAccount:
    def test_create_account_success(self):
        # Arrange
        repo = FakeRepository()

        # Act
        account = create_account(
            repo=repo,
            name="Test Account",
            currency="USD",
            initial_balance=Decimal(100),
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
            repo=repo,
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
            id="existing-id",
            name="Existing Account",
            currency="USD",
            initial_balance=Decimal(100),
        )
        repo = FakeRepository(accounts=[existing])

        # Act & Assert
        with pytest.raises(DuplicateAccountNameError) as exc_info:
            create_account(
                repo=repo,
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
                repo=repo,
                name="Negative Account",
                currency="USD",
                initial_balance=Decimal(-100),
            )

        assert "cannot be negative" in str(exc_info.value)
        assert "-100" in str(exc_info.value)
        assert repo.committed is False  # Should not commit on error
        assert len(repo.accounts) == 0  # Should not add account
