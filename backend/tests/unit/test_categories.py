import pytest
from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import CategoryInUseError
from app.service_layer.services import create_category
from app.service_layer.services import list_categories
from app.service_layer.services import update_category_name
from app.service_layer.services import update_category
from app.service_layer.services import delete_category
from tests.unit.test_services import FakeUnitOfWork
from app.domain.model import Account
from app.domain.model import Category, CategoryType
from decimal import Decimal
from tests.constants import JAN_01
from app.domain.model import PostingType


class TestCategoryType:
    def test_category_type_enum_values(self):
        assert CategoryType.INCOME == "INCOME"
        assert CategoryType.EXPENSE == "EXPENSE"


class TestCategoryDomain:
    def test_create_parent_category(self):
        cat = Category(
            category_id="cat-1",
            name="Food",
            category_type=CategoryType.EXPENSE,
        )
        assert cat.category_id == "cat-1"
        assert cat.name == "Food"
        assert cat.category_type == CategoryType.EXPENSE
        assert cat.parent_id is None

    def test_create_subcategory(self):
        cat = Category(
            category_id="cat-2",
            name="Groceries",
            category_type=CategoryType.EXPENSE,
            parent_id="cat-1",
        )
        assert cat.parent_id == "cat-1"
        assert cat.category_type == CategoryType.EXPENSE

    def test_create_category_with_description(self):
        cat = Category(
            category_id="cat-d1",
            name="Food",
            category_type=CategoryType.EXPENSE,
            description="Monthly groceries",
        )
        assert cat.description == "Monthly groceries"

    def test_create_category_description_defaults_to_none(self):
        cat = Category(
            category_id="cat-d2",
            name="Food",
            category_type=CategoryType.EXPENSE,
        )
        assert cat.description is None

    def test_category_default_parent_id_is_none(self):
        cat = Category(
            category_id="cat-3",
            name="Salary",
            category_type=CategoryType.INCOME,
        )
        assert cat.parent_id is None


class TestCreateCategory:
    def test_create_category_success(self):
        uow = FakeUnitOfWork()
        category = create_category(uow, name="Groceries", category_type=CategoryType.EXPENSE)
        assert category.name == "Groceries"
        assert category.category_type == CategoryType.EXPENSE
        assert uow.committed is True
        assert len(uow.categories._categories) == 1

    def test_create_category_with_description(self):
        uow = FakeUnitOfWork()
        category = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, description="Some desc"
        )
        assert category.description == "Some desc"
        assert uow.committed is True

    def test_create_category_duplicate_name_raises_error(self):
        uow = FakeUnitOfWork()
        create_category(uow, name="Groceries", category_type=CategoryType.EXPENSE)
        with pytest.raises(DuplicateCategoryNameError):
            create_category(uow, name="Groceries", category_type=CategoryType.EXPENSE)
        assert len(uow.categories._categories) == 1


class TestListCategories:
    def test_list_categories_empty(self):
        uow = FakeUnitOfWork()
        assert list_categories(uow) == []

    def test_list_categories_returns_all(self):
        uow = FakeUnitOfWork()
        c1 = create_category(uow, name="C1", category_type=CategoryType.EXPENSE)
        c2 = create_category(uow, name="C2", category_type=CategoryType.INCOME)
        cats = list_categories(uow)
        assert len(cats) == 2
        assert c1 in cats
        assert c2 in cats


class TestUpdateCategory:
    def test_update_category_success(self):
        uow = FakeUnitOfWork()
        category = create_category(uow, name="Groceries", category_type=CategoryType.EXPENSE)
        updated = update_category_name(uow, category_id=category.category_id, new_name="Food")
        assert updated.name == "Food"
        assert uow.committed is True

    def test_update_category_same_name_succeeds(self):
        uow = FakeUnitOfWork()
        category = create_category(uow, name="Groceries", category_type=CategoryType.EXPENSE)
        uow.committed = False
        updated = update_category_name(uow, category_id=category.category_id, new_name="Groceries")
        assert updated.name == "Groceries"
        assert uow.committed is True

    def test_update_category_duplicate_name_raises_error(self):
        uow = FakeUnitOfWork()
        c1 = create_category(uow, name="Groceries", category_type=CategoryType.EXPENSE)
        _c2 = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        uow.committed = False
        with pytest.raises(DuplicateCategoryNameError):
            update_category_name(uow, category_id=c1.category_id, new_name="Food")
        assert c1.name == "Groceries"
        assert uow.committed is False

    def test_update_category_not_found_raises_error(self):
        uow = FakeUnitOfWork()
        with pytest.raises(CategoryNotFoundError):
            update_category_name(uow, category_id="non-existent", new_name="New Name")


class TestDeleteCategory:
    def test_delete_category_success(self):
        uow = FakeUnitOfWork()
        c1 = create_category(uow, name="C1", category_type=CategoryType.EXPENSE)
        delete_category(uow, category_id=c1.category_id)
        assert uow.committed is True
        assert len(uow.categories._categories) == 0

    def test_delete_category_not_found_raises_error(self):
        uow = FakeUnitOfWork()
        with pytest.raises(CategoryNotFoundError):
            delete_category(uow, category_id="non-existent")

    def test_delete_category_in_use_raises_error(self):
        uow = FakeUnitOfWork()
        c1 = create_category(uow, name="C1", category_type=CategoryType.EXPENSE)
        account = Account("a1", "acc", "USD", initial_balance=Decimal(100))
        account.record_posting(
            Decimal(10), JAN_01, category_id=c1.category_id, posting_type=PostingType.EXPENSE
        )
        uow.accounts.add(account)
        with pytest.raises(CategoryInUseError):
            delete_category(uow, category_id=c1.category_id)
        assert len(uow.categories._categories) == 1


class TestUpdateCategoryDescription:
    def test_update_category_description(self):
        uow = FakeUnitOfWork()
        category = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        updated = update_category(
            uow, category_id=category.category_id, description="New desc", update_description=True
        )
        assert updated.description == "New desc"
        assert uow.committed is True

    def test_update_category_clear_description(self):
        uow = FakeUnitOfWork()
        category = create_category(
            uow, name="Food", category_type=CategoryType.EXPENSE, description="Old desc"
        )
        updated = update_category(
            uow,
            category_id=category.category_id,
            description=None,
            update_description=True,
        )
        assert updated.description is None

    def test_update_category_name_and_description(self):
        uow = FakeUnitOfWork()
        category = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        updated = update_category(
            uow,
            category_id=category.category_id,
            name="Groceries",
            description="Weekly groceries",
            update_description=True,
        )
        assert updated.name == "Groceries"
        assert updated.description == "Weekly groceries"


class TestUpdateCategoryParent:
    def test_move_subcategory_to_different_parent(self):
        uow = FakeUnitOfWork()
        parent1 = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        parent2 = create_category(uow, name="Shopping", category_type=CategoryType.EXPENSE)
        child = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent1.category_id
        )

        updated = update_category(
            uow,
            category_id=child.category_id,
            parent_id=parent2.category_id,
            update_parent=True,
        )
        assert updated.parent_id == parent2.category_id

    def test_promote_subcategory_to_root(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        child = create_category(
            uow, name="Groceries", category_type=CategoryType.EXPENSE, parent_id=parent.category_id
        )

        updated = update_category(
            uow,
            category_id=child.category_id,
            parent_id=None,
            update_parent=True,
        )
        assert updated.parent_id is None

    def test_make_root_category_a_subcategory(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        root = create_category(uow, name="Groceries", category_type=CategoryType.EXPENSE)

        updated = update_category(
            uow,
            category_id=root.category_id,
            parent_id=parent.category_id,
            update_parent=True,
        )
        assert updated.parent_id == parent.category_id

    def test_parent_not_found_raises_error(self):
        uow = FakeUnitOfWork()
        child = create_category(uow, name="Groceries", category_type=CategoryType.EXPENSE)

        with pytest.raises(CategoryNotFoundError):
            update_category(
                uow,
                category_id=child.category_id,
                parent_id="non-existent",
                update_parent=True,
            )

    def test_parent_is_subcategory_raises_hierarchy_error(self):
        from app.domain.exceptions import CategoryHierarchyError

        uow = FakeUnitOfWork()
        grandparent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        parent = create_category(
            uow,
            name="Groceries",
            category_type=CategoryType.EXPENSE,
            parent_id=grandparent.category_id,
        )
        orphan = create_category(uow, name="Organic", category_type=CategoryType.EXPENSE)

        with pytest.raises(CategoryHierarchyError, match="max 2 levels"):
            update_category(
                uow,
                category_id=orphan.category_id,
                parent_id=parent.category_id,
                update_parent=True,
            )

    def test_parent_type_mismatch_raises_hierarchy_error(self):
        from app.domain.exceptions import CategoryHierarchyError

        uow = FakeUnitOfWork()
        income_parent = create_category(uow, name="Salary", category_type=CategoryType.INCOME)
        expense_child = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)

        with pytest.raises(CategoryHierarchyError, match="must match"):
            update_category(
                uow,
                category_id=expense_child.category_id,
                parent_id=income_parent.category_id,
                update_parent=True,
            )

    def test_category_with_children_cannot_become_subcategory(self):
        from app.domain.exceptions import CategoryHierarchyError

        uow = FakeUnitOfWork()
        parent_with_children = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        create_category(
            uow,
            name="Groceries",
            category_type=CategoryType.EXPENSE,
            parent_id=parent_with_children.category_id,
        )
        new_parent = create_category(uow, name="Shopping", category_type=CategoryType.EXPENSE)

        with pytest.raises(CategoryHierarchyError, match="has children"):
            update_category(
                uow,
                category_id=parent_with_children.category_id,
                parent_id=new_parent.category_id,
                update_parent=True,
            )

    def test_duplicate_name_in_new_parent_raises_error(self):
        uow = FakeUnitOfWork()
        parent1 = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        parent2 = create_category(uow, name="Shopping", category_type=CategoryType.EXPENSE)
        create_category(
            uow,
            name="Groceries",
            category_type=CategoryType.EXPENSE,
            parent_id=parent2.category_id,
        )
        child = create_category(
            uow,
            name="Groceries",
            category_type=CategoryType.EXPENSE,
            parent_id=parent1.category_id,
        )

        with pytest.raises(DuplicateCategoryNameError):
            update_category(
                uow,
                category_id=child.category_id,
                parent_id=parent2.category_id,
                update_parent=True,
            )

    def test_self_parent_raises_hierarchy_error(self):
        from app.domain.exceptions import CategoryHierarchyError

        uow = FakeUnitOfWork()
        cat = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)

        with pytest.raises(CategoryHierarchyError, match="cannot be its own parent"):
            update_category(
                uow,
                category_id=cat.category_id,
                parent_id=cat.category_id,
                update_parent=True,
            )

    def test_move_to_same_parent_is_noop(self):
        uow = FakeUnitOfWork()
        parent = create_category(uow, name="Food", category_type=CategoryType.EXPENSE)
        child = create_category(
            uow,
            name="Groceries",
            category_type=CategoryType.EXPENSE,
            parent_id=parent.category_id,
        )

        updated = update_category(
            uow,
            category_id=child.category_id,
            parent_id=parent.category_id,
            update_parent=True,
        )
        assert updated.parent_id == parent.category_id
