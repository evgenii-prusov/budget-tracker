from datetime import date
from decimal import Decimal
import pytest

from app.domain.model import Account
from app.domain.model import PostingType
from app.domain.model import Transfer
from app.domain.exceptions import InsufficientFundsError
from app.domain.exceptions import InvalidCurrencyError
from tests.constants import JAN_01


def test_create_account_with_invalid_currency_raises_error():
    with pytest.raises(InvalidCurrencyError, match="Invalid currency: BITCOIN"):
        Account(
            account_id="acc1",
            name="Test Account",
            currency="BITCOIN",
            initial_balance=Decimal(100),
        )


@pytest.mark.parametrize(
    "currency",
    ["eur", "", "US", "123"],
)
def test_create_account_with_invalid_currency_variants(currency):
    with pytest.raises(InvalidCurrencyError, match=f"Invalid currency: {currency}"):
        Account(
            account_id="acc1",
            name="Test Account",
            currency=currency,
            initial_balance=Decimal(100),
        )


def test_create_account_with_valid_currency_succeeds():
    account = Account(
        account_id="acc1",
        name="Test Account",
        currency="EUR",
        initial_balance=Decimal(100),
    )
    assert account.currency == "EUR"


def test_account_balance_is_sum_of_init_balance_and_postings(
    acc_eur: Account,
):
    # Arrange: Record multiple postings of different types
    acc_eur.record_posting(
        Decimal(2), JAN_01, category_id="CAT_1", posting_type=PostingType.EXPENSE
    )
    acc_eur.record_posting(
        Decimal(3), JAN_01, category_id="CAT_2", posting_type=PostingType.EXPENSE
    )
    acc_eur.record_posting(
        Decimal(500), JAN_01, category_id="CAT_3", posting_type=PostingType.INCOME
    )

    # Act: Get account balance
    balance = acc_eur.balance

    # Assert: Balance equals initial balance plus sum of postings
    # Initial: 35, Expenses: -5, Income: +500, Total: 530
    assert balance == Decimal(530)


def test_account_balance_reflects_transfers(acc_eur: Account, acc_rub: Account):
    # Arrange:
    # acc_eur initial: 35
    # acc_rub initial: 0

    # Act: Create transfers using Account methods
    # 1. Outgoing from EUR to RUB: 10 EUR
    t1 = Transfer(None, acc_eur.account_id, acc_rub.account_id, Decimal(10), Decimal(800), JAN_01)
    acc_eur.record_outgoing_transfer(t1)
    acc_rub.record_incoming_transfer(t1)

    # 2. Incoming to EUR from RUB: 5 EUR
    t2 = Transfer(None, acc_rub.account_id, acc_eur.account_id, Decimal(400), Decimal(5), JAN_01)
    acc_rub.record_outgoing_transfer(t2)
    acc_eur.record_incoming_transfer(t2)

    # Assert:
    # acc_eur balance: 35 - 10 + 5 = 30
    # acc_rub balance: 0 + 800 - 400 = 400
    assert acc_eur.balance == Decimal(30)
    assert acc_rub.balance == Decimal(400)


# --- Tests for record_outgoing_transfer / record_incoming_transfer ---


def test_record_outgoing_transfer_updates_balance(acc_eur: Account, acc_rub: Account):
    transfer = Transfer(
        None, acc_eur.account_id, acc_rub.account_id, Decimal(10), Decimal(800), JAN_01
    )
    acc_eur.record_outgoing_transfer(transfer)
    assert acc_eur.balance == Decimal(25)  # 35 - 10


def test_record_outgoing_transfer_insufficient_funds_raises_error(
    acc_eur: Account, acc_rub: Account
):
    transfer = Transfer(
        None, acc_eur.account_id, acc_rub.account_id, Decimal(50), Decimal(4000), JAN_01
    )
    with pytest.raises(InsufficientFundsError):
        acc_eur.record_outgoing_transfer(transfer)
    assert acc_eur.balance == Decimal(35)  # unchanged


def test_record_incoming_transfer_updates_balance(acc_rub: Account, acc_eur: Account):
    transfer = Transfer(
        None, acc_eur.account_id, acc_rub.account_id, Decimal(10), Decimal(800), JAN_01
    )
    acc_rub.record_incoming_transfer(transfer)
    assert acc_rub.balance == Decimal(800)  # 0 + 800


# --- Tests for postings, get_posting, has_postings/transfers, counts ---


def test_postings_property_returns_copy(acc_eur: Account):
    acc_eur.record_posting(Decimal(5), JAN_01, category_id=None, posting_type=PostingType.INCOME)
    postings = acc_eur.postings
    assert len(postings) == 1
    postings.clear()
    assert len(acc_eur.postings) == 1  # internal state unaffected


def test_get_posting_returns_matching_posting(acc_eur: Account):
    posting = acc_eur.record_posting(
        Decimal(5), JAN_01, category_id=None, posting_type=PostingType.INCOME
    )
    found = acc_eur.get_posting(posting.posting_id)
    assert found == posting


def test_get_posting_returns_none_for_unknown_id(acc_eur: Account):
    assert acc_eur.get_posting("nonexistent") is None


def test_has_postings_false_when_empty(acc_eur: Account):
    assert acc_eur.has_postings is False


def test_has_postings_true_after_recording(acc_eur: Account):
    acc_eur.record_posting(Decimal(5), JAN_01, category_id=None, posting_type=PostingType.INCOME)
    assert acc_eur.has_postings is True


def test_has_transfers_false_when_empty(acc_eur: Account):
    assert acc_eur.has_transfers is False


def test_has_transfers_true_after_recording(acc_eur: Account, acc_rub: Account):
    transfer = Transfer(
        None, acc_eur.account_id, acc_rub.account_id, Decimal(10), Decimal(800), JAN_01
    )
    acc_eur.record_outgoing_transfer(transfer)
    assert acc_eur.has_transfers is True


def test_posting_count(acc_eur: Account):
    assert acc_eur.posting_count == 0
    acc_eur.record_posting(Decimal(5), JAN_01, category_id=None, posting_type=PostingType.INCOME)
    acc_eur.record_posting(Decimal(3), JAN_01, category_id=None, posting_type=PostingType.INCOME)
    assert acc_eur.posting_count == 2


def test_transfer_count(acc_eur: Account, acc_rub: Account):
    assert acc_eur.transfer_count == 0
    t1 = Transfer(None, acc_eur.account_id, acc_rub.account_id, Decimal(5), Decimal(400), JAN_01)
    acc_eur.record_outgoing_transfer(t1)
    t2 = Transfer(None, acc_rub.account_id, acc_eur.account_id, Decimal(200), Decimal(3), JAN_01)
    acc_eur.record_incoming_transfer(t2)
    assert acc_eur.transfer_count == 2


def test_account_is_savings_default_false():
    account = Account(
        account_id="acc1",
        name="Test Account",
        currency="EUR",
        initial_balance=Decimal(100),
    )
    assert account.is_savings is False


def test_account_is_savings_set_true():
    account = Account(
        account_id="acc1",
        name="Savings Account",
        currency="EUR",
        initial_balance=Decimal(100),
        is_savings=True,
    )
    assert account.is_savings is True


def test_record_posting_with_payee_and_description(acc_eur: Account):
    posting = acc_eur.record_posting(
        Decimal(5),
        JAN_01,
        category_id=None,
        posting_type=PostingType.INCOME,
        payee="Acme Corp",
        description="January salary",
    )
    assert posting.payee == "Acme Corp"
    assert posting.description == "January salary"


def test_record_posting_payee_description_default_none(acc_eur: Account):
    posting = acc_eur.record_posting(
        Decimal(5),
        JAN_01,
        category_id=None,
        posting_type=PostingType.INCOME,
    )
    assert posting.payee is None
    assert posting.description is None


def test_account_description_default_none():
    account = Account(
        account_id="acc1",
        name="Test Account",
        currency="EUR",
        initial_balance=Decimal(100),
    )
    assert account.description is None


def test_account_description_set():
    account = Account(
        account_id="acc1",
        name="Test Account",
        currency="EUR",
        initial_balance=Decimal(100),
        description="My main spending account",
    )
    assert account.description == "My main spending account"


# --- Tests for update_posting ---


class TestUpdatePosting:
    def test_update_posting_amount(self, acc_eur: Account):
        """Changing amount from 5 to 10 should update balance accordingly."""
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
        )
        # balance: 35 - 5 = 30
        assert acc_eur.balance == Decimal(30)

        updated = acc_eur.update_posting(posting.posting_id, amount=Decimal(10))

        assert updated.amount == Decimal("-10")
        assert acc_eur.balance == Decimal(25)  # 35 - 10

    def test_update_posting_date(self, acc_eur: Account):
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
        )
        new_date = date(2024, 6, 15)

        updated = acc_eur.update_posting(posting.posting_id, posting_date=new_date)

        assert updated.posting_date == new_date
        assert updated.amount == Decimal("-5")  # unchanged

    def test_update_posting_type_expense_to_income(self, acc_eur: Account):
        """Changing EXPENSE→INCOME should flip the sign and update balance."""
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
        )
        # balance: 35 - 5 = 30
        assert acc_eur.balance == Decimal(30)

        updated = acc_eur.update_posting(posting.posting_id, posting_type=PostingType.INCOME)

        assert updated.posting_type == PostingType.INCOME
        assert updated.amount == Decimal("5")  # flipped to positive
        assert acc_eur.balance == Decimal(40)  # 35 + 5

    def test_update_posting_amount_and_type_together(self, acc_eur: Account):
        """Changing both amount and type at once."""
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
        )
        # balance: 35 - 5 = 30

        updated = acc_eur.update_posting(
            posting.posting_id,
            amount=Decimal(20),
            posting_type=PostingType.INCOME,
        )

        assert updated.amount == Decimal("20")
        assert updated.posting_type == PostingType.INCOME
        assert acc_eur.balance == Decimal(55)  # 35 + 20

    def test_update_posting_category(self, acc_eur: Account):
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id="CAT_1", posting_type=PostingType.EXPENSE
        )

        updated = acc_eur.update_posting(
            posting.posting_id, category_id="CAT_2", update_category=True
        )

        assert updated.category_id == "CAT_2"

    def test_update_posting_clear_category(self, acc_eur: Account):
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id="CAT_1", posting_type=PostingType.EXPENSE
        )

        updated = acc_eur.update_posting(posting.posting_id, category_id=None, update_category=True)

        assert updated.category_id is None

    def test_update_posting_payee(self, acc_eur: Account):
        posting = acc_eur.record_posting(
            Decimal(5),
            JAN_01,
            category_id=None,
            posting_type=PostingType.INCOME,
            payee="Old Payee",
        )

        updated = acc_eur.update_posting(posting.posting_id, payee="New Payee", update_payee=True)

        assert updated.payee == "New Payee"

    def test_update_posting_clear_payee(self, acc_eur: Account):
        posting = acc_eur.record_posting(
            Decimal(5),
            JAN_01,
            category_id=None,
            posting_type=PostingType.INCOME,
            payee="Some Payee",
        )

        updated = acc_eur.update_posting(posting.posting_id, payee=None, update_payee=True)

        assert updated.payee is None

    def test_update_posting_description(self, acc_eur: Account):
        posting = acc_eur.record_posting(
            Decimal(5),
            JAN_01,
            category_id=None,
            posting_type=PostingType.INCOME,
            description="Old desc",
        )

        updated = acc_eur.update_posting(
            posting.posting_id, description="New desc", update_description=True
        )

        assert updated.description == "New desc"

    def test_update_posting_insufficient_funds(self, acc_eur: Account):
        """Increasing expense amount beyond balance should raise."""
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
        )
        # balance: 35 - 5 = 30

        with pytest.raises(InsufficientFundsError):
            acc_eur.update_posting(posting.posting_id, amount=Decimal(100))

        # Posting should be unchanged after failed update
        assert posting.amount == Decimal("-5")
        assert acc_eur.balance == Decimal(30)

    def test_update_posting_not_found(self, acc_eur: Account):
        from app.domain.exceptions import PostingNotFoundError

        with pytest.raises(PostingNotFoundError):
            acc_eur.update_posting("nonexistent-id", amount=Decimal(10))

    def test_update_posting_no_changes(self, acc_eur: Account):
        """Calling update with no fields should return posting unchanged."""
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
        )

        updated = acc_eur.update_posting(posting.posting_id)

        assert updated.amount == Decimal("-5")
        assert acc_eur.balance == Decimal(30)

    def test_update_posting_returns_same_object(self, acc_eur: Account):
        """The returned posting should be the same object (mutated in-place)."""
        posting = acc_eur.record_posting(
            Decimal(5), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
        )

        updated = acc_eur.update_posting(posting.posting_id, amount=Decimal(10))

        assert updated is posting
