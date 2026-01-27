import pytest
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import CategoryInUseError
from app.service_layer.services import create_category
from app.service_layer.services import list_categories
from app.service_layer.services import delete_category
from tests.unit.test_services import FakeRepository
from app.domain.model import Account
from decimal import Decimal
from tests.constants import JAN_01
from app.domain.model import PostingType


class TestCreateCategory:
    def test_create_category_success(self):
        # Arrange
        repo = FakeRepository()

        # Act
        category = create_category(repo, name="Groceries")

        # Assert
        assert category.name == "Groceries"
        assert repo.committed is True
        assert len(repo.categories) == 1

    def test_create_category_duplicate_name_raises_error(self):
        # Arrange
        repo = FakeRepository()
        create_category(repo, name="Groceries")

        # Act & Assert
        with pytest.raises(DuplicateCategoryNameError):
            create_category(repo, name="Groceries")

        assert len(repo.categories) == 1


class TestListCategories:
    def test_list_categories_empty(self):
        # Arrange
        repo = FakeRepository()

        # Act & Assert
        assert list_categories(repo) == []

    def test_list_categories_returns_all(self):
        # Arrange
        repo = FakeRepository()
        c1 = create_category(repo, name="C1")
        c2 = create_category(repo, name="C2")

        # Act
        cats = list_categories(repo)

        # Assert
        assert len(cats) == 2
        assert c1 in cats
        assert c2 in cats


class TestDeleteCategory:
    def test_delete_category_success(self):
        # Arrange
        repo = FakeRepository()
        c1 = create_category(repo, name="C1")

        # Act
        delete_category(repo, category_id=c1.category_id)

        # Assert
        assert repo.committed is True
        assert len(repo.categories) == 0

    def test_delete_category_not_found_raises_error(self):
        # Arrange
        repo = FakeRepository()

        # Act & Assert
        with pytest.raises(CategoryNotFoundError):
            delete_category(repo, category_id="non-existent")

    def test_delete_category_in_use_raises_error(self):
        # Arrange
        repo = FakeRepository()
        c1 = create_category(repo, name="C1")

        # Create an account and add a posting using this category
        account = Account("a1", "acc", "USD", initial_balance=Decimal(100))
        account.record_posting(
            Decimal(10),
            JAN_01,
            category_id=c1.category_id,
            posting_type=PostingType.EXPENSE,
        )
        repo.add(account)

        # Act & Assert
        with pytest.raises(CategoryInUseError):
            delete_category(repo, category_id=c1.category_id)

        assert len(repo.categories) == 1
