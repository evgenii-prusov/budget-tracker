import pytest
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import CategoryInUseError
from app.service_layer.services import create_category
from app.service_layer.services import list_categories
from app.service_layer.services import update_category_name
from app.service_layer.services import delete_category
from tests.unit.test_services import FakeUnitOfWork
from app.domain.model import Account
from decimal import Decimal
from tests.constants import JAN_01
from app.domain.model import PostingType


class TestCreateCategory:
    def test_create_category_success(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act
        category = create_category(uow, name="Groceries")

        # Assert
        assert category.name == "Groceries"
        assert uow.committed is True
        assert len(uow.repo.categories) == 1

    def test_create_category_duplicate_name_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()
        create_category(uow, name="Groceries")

        # Act & Assert
        with pytest.raises(DuplicateCategoryNameError):
            create_category(uow, name="Groceries")

        assert len(uow.repo.categories) == 1


class TestListCategories:
    def test_list_categories_empty(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
        assert list_categories(uow) == []

    def test_list_categories_returns_all(self):
        # Arrange
        uow = FakeUnitOfWork()
        c1 = create_category(uow, name="C1")
        c2 = create_category(uow, name="C2")

        # Act
        cats = list_categories(uow)

        # Assert
        assert len(cats) == 2
        assert c1 in cats
        assert c2 in cats


class TestUpdateCategory:
    def test_update_category_success(self):
        # Arrange
        uow = FakeUnitOfWork()
        category = create_category(uow, name="Groceries")

        # Act
        updated = update_category_name(
            uow, category_id=category.category_id, new_name="Food"
        )

        # Assert
        assert updated.name == "Food"
        assert uow.committed is True

    def test_update_category_same_name_succeeds(self):
        # Arrange
        uow = FakeUnitOfWork()
        category = create_category(uow, name="Groceries")
        uow.committed = False

        # Act - update to same name
        updated = update_category_name(
            uow,
            category_id=category.category_id,
            new_name="Groceries",
        )

        # Assert
        assert updated.name == "Groceries"
        assert uow.committed is True

    def test_update_category_duplicate_name_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()
        c1 = create_category(uow, name="Groceries")
        _c2 = create_category(uow, name="Food")
        uow.committed = False

        # Act & Assert
        with pytest.raises(DuplicateCategoryNameError):
            update_category_name(
                uow,
                category_id=c1.category_id,
                new_name="Food",
            )

        assert c1.name == "Groceries"
        assert uow.committed is False

    def test_update_category_not_found_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
        with pytest.raises(CategoryNotFoundError):
            update_category_name(
                uow,
                category_id="non-existent",
                new_name="New Name",
            )


class TestDeleteCategory:
    def test_delete_category_success(self):
        # Arrange
        uow = FakeUnitOfWork()
        c1 = create_category(uow, name="C1")

        # Act
        delete_category(uow, category_id=c1.category_id)

        # Assert
        assert uow.committed is True
        assert len(uow.repo.categories) == 0

    def test_delete_category_not_found_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()

        # Act & Assert
        with pytest.raises(CategoryNotFoundError):
            delete_category(uow, category_id="non-existent")

    def test_delete_category_in_use_raises_error(self):
        # Arrange
        uow = FakeUnitOfWork()
        c1 = create_category(uow, name="C1")

        # Create an account and add a posting using this category
        account = Account("a1", "acc", "USD", initial_balance=Decimal(100))
        account.record_posting(
            Decimal(10),
            JAN_01,
            category_id=c1.category_id,
            posting_type=PostingType.EXPENSE,
        )
        uow.repo.add(account)

        # Act & Assert
        with pytest.raises(CategoryInUseError):
            delete_category(uow, category_id=c1.category_id)

        assert len(uow.repo.categories) == 1
