from decimal import Decimal

import pytest

from app.domain.model import Account, Category, CategoryType
from app.mcp.resolvers import (
    resolve_account_by_currency,
    resolve_account_by_name,
    resolve_parent_category_by_name,
    resolve_subcategory_by_name,
)
from app.mcp.server import (
    _add_expense_impl,
    _add_income_impl,
    _create_account_impl,
    _create_category_impl,
    _get_spending_report_impl,
    _list_accounts_impl,
    _transfer_funds_impl,
)
from tests.constants import JAN_01

# --------------- helpers reused from test_services.py --------------- #
from tests.unit.test_services import FakeUnitOfWork


class TestResolveAccountByName:
    def test_resolves_existing_account(self):
        uow = FakeUnitOfWork()
        acc = Account(None, "Cash EUR", "EUR", Decimal("1000"))
        uow.accounts.add(acc)
        result = resolve_account_by_name(uow, "Cash EUR")
        assert result.account_id == acc.account_id

    def test_case_insensitive(self):
        uow = FakeUnitOfWork()
        acc = Account(None, "Cash EUR", "EUR", Decimal("1000"))
        uow.accounts.add(acc)
        result = resolve_account_by_name(uow, "cash eur")
        assert result.account_id == acc.account_id

    def test_raises_when_not_found(self):
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("1000")))
        with pytest.raises(ValueError, match="No account named 'Nonexistent'"):
            resolve_account_by_name(uow, "Nonexistent")

    def test_error_lists_available_accounts(self):
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("100")))
        uow.accounts.add(Account(None, "Savings USD", "USD", Decimal("200")))
        with pytest.raises(ValueError, match="Available.*Cash EUR.*Savings USD"):
            resolve_account_by_name(uow, "Nonexistent")


class TestResolveAccountByCurrency:
    def test_resolves_non_savings_account(self):
        uow = FakeUnitOfWork()
        savings = Account(None, "Savings EUR", "EUR", Decimal("5000"), is_savings=True)
        checking = Account(None, "Cash EUR", "EUR", Decimal("1000"), is_savings=False)
        uow.accounts.add(savings)
        uow.accounts.add(checking)
        result = resolve_account_by_currency(uow, "EUR")
        assert result.account_id == checking.account_id

    def test_falls_back_to_savings_if_no_non_savings(self):
        uow = FakeUnitOfWork()
        savings = Account(None, "Savings EUR", "EUR", Decimal("5000"), is_savings=True)
        uow.accounts.add(savings)
        result = resolve_account_by_currency(uow, "EUR")
        assert result.account_id == savings.account_id

    def test_case_insensitive_currency(self):
        uow = FakeUnitOfWork()
        acc = Account(None, "Cash EUR", "EUR", Decimal("1000"))
        uow.accounts.add(acc)
        result = resolve_account_by_currency(uow, "eur")
        assert result.account_id == acc.account_id

    def test_raises_when_no_account_with_currency(self):
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("100")))
        with pytest.raises(ValueError, match="No account with currency 'USD'"):
            resolve_account_by_currency(uow, "USD")

    def test_error_lists_available_currencies(self):
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("100")))
        uow.accounts.add(Account(None, "Cash GBP", "GBP", Decimal("200")))
        with pytest.raises(ValueError, match="Available.*EUR.*GBP"):
            resolve_account_by_currency(uow, "USD")


class TestResolveSubcategoryByName:
    def _make_category_tree(self, uow: FakeUnitOfWork):
        parent = Category(None, "Food", CategoryType.EXPENSE)
        sub = Category(None, "Groceries", CategoryType.EXPENSE, parent_id=parent.category_id)
        uow.categories.add(parent)
        uow.categories.add(sub)
        return parent, sub

    def test_resolves_subcategory(self):
        uow = FakeUnitOfWork()
        _, sub = self._make_category_tree(uow)
        result = resolve_subcategory_by_name(uow, "Groceries")
        assert result.category_id == sub.category_id

    def test_case_insensitive(self):
        uow = FakeUnitOfWork()
        _, sub = self._make_category_tree(uow)
        result = resolve_subcategory_by_name(uow, "groceries")
        assert result.category_id == sub.category_id

    def test_ignores_parent_categories(self):
        uow = FakeUnitOfWork()
        self._make_category_tree(uow)
        with pytest.raises(ValueError, match="No subcategory named 'Food'"):
            resolve_subcategory_by_name(uow, "Food")

    def test_raises_when_not_found(self):
        uow = FakeUnitOfWork()
        self._make_category_tree(uow)
        with pytest.raises(ValueError, match="No subcategory named 'Unknown'"):
            resolve_subcategory_by_name(uow, "Unknown")

    def test_error_lists_available_subcategories(self):
        uow = FakeUnitOfWork()
        self._make_category_tree(uow)
        with pytest.raises(ValueError, match="Available.*Groceries"):
            resolve_subcategory_by_name(uow, "Unknown")

    def test_filters_by_category_type(self):
        uow = FakeUnitOfWork()
        # Create EXPENSE subcategory "Groceries"
        exp_parent = Category(None, "Food", CategoryType.EXPENSE)
        exp_sub = Category(
            None, "Groceries", CategoryType.EXPENSE, parent_id=exp_parent.category_id
        )
        # Create INCOME subcategory also named "Groceries"
        inc_parent = Category(None, "Side Income", CategoryType.INCOME)
        inc_sub = Category(None, "Groceries", CategoryType.INCOME, parent_id=inc_parent.category_id)
        uow.categories.add(exp_parent)
        uow.categories.add(exp_sub)
        uow.categories.add(inc_parent)
        uow.categories.add(inc_sub)

        result = resolve_subcategory_by_name(uow, "Groceries", category_type=CategoryType.EXPENSE)
        assert result.category_id == exp_sub.category_id
        assert result.category_type == CategoryType.EXPENSE


class TestResolveParentCategoryByName:
    def test_resolves_existing_parent(self):
        uow = FakeUnitOfWork()
        parent = Category(None, "Food", CategoryType.EXPENSE)
        uow.categories.add(parent)
        result = resolve_parent_category_by_name(uow, "Food")
        assert result.category_id == parent.category_id

    def test_case_insensitive(self):
        uow = FakeUnitOfWork()
        parent = Category(None, "Food", CategoryType.EXPENSE)
        uow.categories.add(parent)
        result = resolve_parent_category_by_name(uow, "food")
        assert result.category_id == parent.category_id

    def test_ignores_subcategories(self):
        uow = FakeUnitOfWork()
        parent = Category(None, "Food", CategoryType.EXPENSE)
        sub = Category(None, "Groceries", CategoryType.EXPENSE, parent_id=parent.category_id)
        uow.categories.add(parent)
        uow.categories.add(sub)
        with pytest.raises(ValueError, match="No parent category named 'Groceries'"):
            resolve_parent_category_by_name(uow, "Groceries")

    def test_raises_when_not_found(self):
        uow = FakeUnitOfWork()
        uow.categories.add(Category(None, "Food", CategoryType.EXPENSE))
        with pytest.raises(ValueError, match="No parent category named 'Unknown'"):
            resolve_parent_category_by_name(uow, "Unknown")

    def test_filters_by_category_type(self):
        uow = FakeUnitOfWork()
        exp_parent = Category(None, "Food", CategoryType.EXPENSE)
        inc_parent = Category(None, "Salary", CategoryType.INCOME)
        uow.categories.add(exp_parent)
        uow.categories.add(inc_parent)

        result = resolve_parent_category_by_name(uow, "Food", category_type=CategoryType.EXPENSE)
        assert result.category_id == exp_parent.category_id

        with pytest.raises(ValueError, match=r"No parent category named 'Food' \(type=INCOME\)"):
            resolve_parent_category_by_name(uow, "Food", category_type=CategoryType.INCOME)


# ==================== Tool implementation tests ==================== #


class TestCreateCategoryImpl:
    def test_creates_parent_category(self):
        uow = FakeUnitOfWork()
        result = _create_category_impl(uow, name="Food", category_type_str="expense")
        assert "Created EXPENSE parent category 'Food'" in result
        assert len(uow.categories.list_parents()) == 1
        assert uow.categories.list_parents()[0].name == "Food"

    def test_creates_subcategory(self):
        uow = FakeUnitOfWork()
        uow.categories.add(Category(None, "Food", CategoryType.EXPENSE))

        result = _create_category_impl(
            uow, name="Groceries", category_type_str="expense", parent_name="Food"
        )
        assert "Created EXPENSE subcategory 'Groceries' under 'Food'" in result

        parent = uow.categories.list_parents()[0]
        subs = uow.categories.list_children(parent.category_id)
        assert len(subs) == 1
        assert subs[0].name == "Groceries"

    def test_invalid_category_type(self):
        uow = FakeUnitOfWork()
        result = _create_category_impl(uow, name="Food", category_type_str="invalid")
        assert "Invalid category type" in result

    def test_duplicate_category_name(self):
        uow = FakeUnitOfWork()
        uow.categories.add(Category(None, "Food", CategoryType.EXPENSE))
        result = _create_category_impl(uow, name="Food", category_type_str="expense")
        assert "already exists" in result

    def test_parent_not_found(self):
        uow = FakeUnitOfWork()
        result = _create_category_impl(
            uow, name="Groceries", category_type_str="expense", parent_name="Nonexistent"
        )
        assert "No parent category named 'Nonexistent'" in result

    def test_mismatched_type_with_parent(self):
        uow = FakeUnitOfWork()
        uow.categories.add(Category(None, "Food", CategoryType.EXPENSE))
        # Resolve parent by name will fail because it filters by type
        result = _create_category_impl(
            uow, name="Groceries", category_type_str="income", parent_name="Food"
        )
        assert "No parent category named 'Food' (type=INCOME)" in result


def _setup_expense_uow() -> FakeUnitOfWork:
    """Helper: UoW with one EUR account and a Groceries subcategory."""
    uow = FakeUnitOfWork()
    acc = Account(None, "Cash EUR", "EUR", Decimal("1000"))
    uow.accounts.add(acc)

    parent = Category(None, "Food", CategoryType.EXPENSE)
    sub = Category(None, "Groceries", CategoryType.EXPENSE, parent_id=parent.category_id)
    uow.categories.add(parent)
    uow.categories.add(sub)
    return uow


class TestCreateAccountImpl:
    def test_creates_account(self):
        uow = FakeUnitOfWork()
        result = _create_account_impl(
            uow,
            name="New Account",
            currency="EUR",
            initial_balance=Decimal("100"),
            is_savings=True,
        )
        assert "Created account 'New Account'" in result
        assert "(savings)" in result
        assert "100" in result

        acc = uow.accounts.get_by_name("New Account")
        assert acc is not None
        assert acc.currency == "EUR"
        assert acc.is_savings is True

    def test_duplicate_name_error(self):
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Existing", "EUR", Decimal("0")))
        result = _create_account_impl(
            uow, name="Existing", currency="USD", initial_balance=Decimal("0")
        )
        assert "already exists" in result.lower()

    def test_negative_balance_error(self):
        uow = FakeUnitOfWork()
        result = _create_account_impl(
            uow, name="Bad Account", currency="EUR", initial_balance=Decimal("-10")
        )
        assert "negative" in result.lower()


class TestAddExpenseImpl:
    def test_records_expense_by_currency(self):
        uow = _setup_expense_uow()
        result = _add_expense_impl(
            uow,
            amount=Decimal("42.50"),
            currency="EUR",
            subcategory="Groceries",
            posting_date=JAN_01,
            description="Weekly shopping",
        )
        assert "42.50" in result
        assert "Cash EUR" in result

    def test_records_expense_by_account_name(self):
        uow = _setup_expense_uow()
        result = _add_expense_impl(
            uow,
            amount=Decimal("42.50"),
            account_name="Cash EUR",
            subcategory="Groceries",
            posting_date=JAN_01,
        )
        assert "42.50" in result
        assert "Cash EUR" in result

    def test_records_expense_with_payee(self):
        uow = _setup_expense_uow()
        result = _add_expense_impl(
            uow,
            amount=Decimal("10"),
            currency="EUR",
            subcategory="Groceries",
            posting_date=JAN_01,
            payee="Lidl",
        )
        assert "Lidl" in result

    def test_balance_decreases_after_expense(self):
        uow = _setup_expense_uow()
        acc = uow.accounts.list_all()[0]
        _add_expense_impl(
            uow,
            amount=Decimal("100"),
            currency="EUR",
            subcategory="Groceries",
            posting_date=JAN_01,
        )
        assert acc.balance == Decimal("900")

    def test_insufficient_funds_error(self):
        uow = _setup_expense_uow()
        result = _add_expense_impl(
            uow,
            amount=Decimal("9999"),
            currency="EUR",
            subcategory="Groceries",
            posting_date=JAN_01,
        )
        assert "Insufficient" in result or "insufficient" in result.lower()

    def test_unknown_subcategory_error(self):
        uow = _setup_expense_uow()
        result = _add_expense_impl(
            uow,
            amount=Decimal("10"),
            currency="EUR",
            subcategory="Nonexistent",
            posting_date=JAN_01,
        )
        assert "No subcategory" in result

    def test_unknown_currency_error(self):
        uow = _setup_expense_uow()
        result = _add_expense_impl(
            uow,
            amount=Decimal("10"),
            currency="JPY",
            subcategory="Groceries",
            posting_date=JAN_01,
        )
        assert "No account" in result

    def test_income_subcategory_returns_friendly_error(self):
        """INCOME subcategory with same name as EXPENSE one should not crash."""
        uow = _setup_expense_uow()
        # Add an INCOME subcategory named "Groceries" (same name as the EXPENSE one)
        inc_parent = Category(None, "Side Income", CategoryType.INCOME)
        inc_sub = Category(None, "Groceries", CategoryType.INCOME, parent_id=inc_parent.category_id)
        uow.categories.add(inc_parent)
        uow.categories.add(inc_sub)

        # Remove the EXPENSE "Groceries" so only INCOME one remains
        uow.categories._categories = [
            c
            for c in uow.categories._categories
            if not (c.name == "Groceries" and c.category_type == CategoryType.EXPENSE)
        ]

        result = _add_expense_impl(
            uow,
            amount=Decimal("10"),
            currency="EUR",
            subcategory="Groceries",
            posting_date=JAN_01,
        )
        # Should return a friendly error string, not crash with CategoryHierarchyError
        assert "No" in result and "subcategory" in result.lower()

    def test_no_account_identifier_error(self):
        uow = _setup_expense_uow()
        result = _add_expense_impl(
            uow,
            amount=Decimal("100"),
            subcategory="Groceries",
            posting_date=JAN_01,
        )
        assert "account_name or currency must be provided" in result.lower()


class TestAddIncomeImpl:
    def _setup_income_uow(self) -> FakeUnitOfWork:
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("1000")))

        parent = Category(None, "Income", CategoryType.INCOME)
        sub = Category(None, "Salary", CategoryType.INCOME, parent_id=parent.category_id)
        uow.categories.add(parent)
        uow.categories.add(sub)
        return uow

    def test_records_income_by_currency(self):
        uow = self._setup_income_uow()
        result = _add_income_impl(
            uow,
            amount=Decimal("2500"),
            currency="EUR",
            subcategory="Salary",
            posting_date=JAN_01,
        )
        assert "2500" in result
        assert "Cash EUR" in result
        assert "income" in result.lower()

    def test_records_income_by_account_name(self):
        uow = self._setup_income_uow()
        result = _add_income_impl(
            uow,
            amount=Decimal("2500"),
            account_name="Cash EUR",
            subcategory="Salary",
            posting_date=JAN_01,
        )
        assert "Cash EUR" in result

    def test_balance_increases_after_income(self):
        uow = self._setup_income_uow()
        acc = uow.accounts.list_all()[0]
        _add_income_impl(
            uow,
            amount=Decimal("500"),
            currency="EUR",
            subcategory="Salary",
            posting_date=JAN_01,
        )
        assert acc.balance == Decimal("1500")

    def test_unknown_subcategory_error(self):
        uow = self._setup_income_uow()
        result = _add_income_impl(
            uow,
            amount=Decimal("10"),
            currency="EUR",
            subcategory="Nonexistent",
            posting_date=JAN_01,
        )
        assert "No subcategory" in result

    def test_expense_subcategory_returns_friendly_error(self):
        uow = self._setup_income_uow()
        # Add an EXPENSE subcategory named "Salary"
        exp_parent = Category(None, "Fixed", CategoryType.EXPENSE)
        exp_sub = Category(None, "Salary", CategoryType.EXPENSE, parent_id=exp_parent.category_id)
        uow.categories.add(exp_parent)
        uow.categories.add(exp_sub)

        # Remove the INCOME "Salary"
        uow.categories._categories = [
            c
            for c in uow.categories._categories
            if not (c.name == "Salary" and c.category_type == CategoryType.INCOME)
        ]

        result = _add_income_impl(
            uow,
            amount=Decimal("10"),
            currency="EUR",
            subcategory="Salary",
            posting_date=JAN_01,
        )
        assert "No" in result and "subcategory" in result.lower()

    def test_no_account_identifier_error(self):
        uow = self._setup_income_uow()
        result = _add_income_impl(
            uow,
            amount=Decimal("100"),
            subcategory="Salary",
            posting_date=JAN_01,
        )
        assert "account_name or currency must be provided" in result.lower()


class TestTransferFundsImpl:
    def _setup_transfer_uow(self) -> FakeUnitOfWork:
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("1000")))
        uow.accounts.add(Account(None, "Savings EUR", "EUR", Decimal("5000"), is_savings=True))
        return uow

    def test_same_currency_transfer(self):
        uow = self._setup_transfer_uow()
        result = _transfer_funds_impl(
            uow,
            from_account="Cash EUR",
            to_account="Savings EUR",
            amount=Decimal("200"),
            transfer_date=JAN_01,
        )
        assert "200" in result
        assert "Cash EUR" in result
        assert "Savings EUR" in result

    def test_cross_currency_transfer(self):
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("1000")))
        uow.accounts.add(Account(None, "Cash USD", "USD", Decimal("500")))
        result = _transfer_funds_impl(
            uow,
            from_account="Cash EUR",
            to_account="Cash USD",
            amount=Decimal("100"),
            to_amount=Decimal("110"),
            transfer_date=JAN_01,
        )
        assert "100" in result
        assert "110" in result

    def test_unknown_source_account(self):
        uow = self._setup_transfer_uow()
        result = _transfer_funds_impl(
            uow,
            from_account="Nonexistent",
            to_account="Savings EUR",
            amount=Decimal("100"),
            transfer_date=JAN_01,
        )
        assert "No account" in result

    def test_insufficient_funds(self):
        uow = self._setup_transfer_uow()
        result = _transfer_funds_impl(
            uow,
            from_account="Cash EUR",
            to_account="Savings EUR",
            amount=Decimal("99999"),
            transfer_date=JAN_01,
        )
        assert "Insufficient" in result or "insufficient" in result.lower()

    def test_zero_amount_error(self):
        uow = self._setup_transfer_uow()
        result = _transfer_funds_impl(
            uow,
            from_account="Cash EUR",
            to_account="Savings EUR",
            amount=Decimal("0"),
            transfer_date=JAN_01,
        )
        assert isinstance(result, str)
        assert result  # non-empty error message

    def test_negative_amount_error(self):
        uow = self._setup_transfer_uow()
        result = _transfer_funds_impl(
            uow,
            from_account="Cash EUR",
            to_account="Savings EUR",
            amount=Decimal("-10"),
            transfer_date=JAN_01,
        )
        assert isinstance(result, str)
        assert result  # non-empty error message


class TestGetSpendingReportImpl:
    def test_returns_report_text(self):
        uow = FakeUnitOfWork()
        result = _get_spending_report_impl(uow, period="month")
        assert "month" in result.lower() or "spending" in result.lower()

    def test_invalid_period(self):
        uow = FakeUnitOfWork()
        result = _get_spending_report_impl(uow, period="decade")
        assert "Invalid" in result or "invalid" in result.lower()


class TestListAccountsImpl:
    def test_lists_all_accounts(self):
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("1000")))
        uow.accounts.add(Account(None, "Savings USD", "USD", Decimal("5000"), is_savings=True))
        result = _list_accounts_impl(uow)
        assert "Cash EUR" in result
        assert "Savings USD" in result
        assert "1000" in result or "1,000" in result

    def test_savings_filter(self):
        uow = FakeUnitOfWork()
        uow.accounts.add(Account(None, "Cash EUR", "EUR", Decimal("1000")))
        uow.accounts.add(Account(None, "Savings USD", "USD", Decimal("5000"), is_savings=True))
        result = _list_accounts_impl(uow, filter="savings")
        assert "Savings USD" in result
        assert "Cash EUR" not in result

    def test_empty_accounts(self):
        uow = FakeUnitOfWork()
        result = _list_accounts_impl(uow)
        assert result == "No accounts found."
