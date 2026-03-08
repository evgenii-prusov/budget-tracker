"""
Domain models for budget tracking.

Type Validation Strategy:
    All monetary values (amounts, balances) must be Decimal instances.
    This is enforced at runtime in constructors and public methods to:
    - Prevent floating-point precision issues in financial calculations
    - Catch type errors early (fail-fast principle)
    - Ensure domain model integrity regardless of caller

    The API layer uses Pydantic which handles JSON-to-Decimal conversion
    before values reach the domain layer.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4
from datetime import date
from enum import StrEnum
import functools

from app.domain.exceptions import InsufficientFundsError
from app.domain.exceptions import InvalidCurrencyError


class PostingType(StrEnum):
    """Types for financial postings."""

    EXPENSE = "EXPENSE"
    INCOME = "INCOME"


class CategoryType(StrEnum):
    """Types for categories (income or expense)."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


VALID_CURRENCIES = frozenset({"USD", "EUR", "GBP", "RUB", "CHF", "JPY", "CNY"})


class Category:
    """Represents a transaction category."""

    def __init__(
        self,
        category_id: str | None,
        name: str,
        category_type: CategoryType,
        parent_id: str | None = None,
    ):
        self.category_id = category_id or str(uuid4())
        self.name = name
        self.category_type = category_type
        self.parent_id = parent_id

    def __repr__(self) -> str:
        return f"Category({self.category_id!r}, {self.name!r})"

    def __eq__(self, other):
        if not isinstance(other, Category):
            return False
        return self.category_id == other.category_id

    def __hash__(self):
        return hash(self.category_id)


@functools.total_ordering
class Transfer:
    """Represents a transfer of funds between two accounts.

    Unlike Posting, a Transfer is a single record that links two accounts.
    No posting records are created for transfers.
    """

    def __init__(
        self,
        transfer_id: str | None,
        source_account_id: str,
        dest_account_id: str,
        debit_amount: Decimal,
        credit_amount: Decimal,
        transfer_date: date,
        description: str | None = None,
    ):
        if not isinstance(debit_amount, Decimal):
            raise TypeError(
                f"debit_amount must be Decimal, got {type(debit_amount).__name__}. "
                f"Use Decimal(str(value)) to convert."
            )
        if not isinstance(credit_amount, Decimal):
            raise TypeError(
                f"credit_amount must be Decimal, got {type(credit_amount).__name__}. "
                f"Use Decimal(str(value)) to convert."
            )
        if debit_amount <= 0 or credit_amount <= 0:
            raise ValueError("Amounts must be greater than zero")

        self.transfer_id = transfer_id or str(uuid4())
        self.source_account_id = source_account_id
        self.dest_account_id = dest_account_id
        self.debit_amount = debit_amount
        self.credit_amount = credit_amount
        self.transfer_date = transfer_date
        self.description = description

    def __repr__(self) -> str:
        return (
            f"Transfer({self.transfer_id!r}, {self.source_account_id!r}, "
            f"{self.dest_account_id!r}, {self.debit_amount!r}, "
            f"{self.credit_amount!r}, {self.transfer_date!r})"
        )

    def __eq__(self, other):
        if not isinstance(other, Transfer):
            return False
        return self.transfer_id == other.transfer_id

    def __hash__(self):
        return hash(self.transfer_id)

    def __lt__(self, other: Transfer):
        return self.transfer_date < other.transfer_date


@functools.total_ordering
class Posting:
    """Represents an income or expense posting on an account.

    The amount is stored as-is (positive or negative). The caller is
    responsible for ensuring the amount has the correct sign based on
    the posting_type. Use Account.record_posting() to automatically
    apply sign logic.
    """

    def __init__(
        self,
        posting_id: str | None,
        account_id: str,
        amount: Decimal,
        posting_date: date,
        category_id: str | None,
        posting_type: PostingType,
        payee: str | None = None,
        description: str | None = None,
    ):
        if not isinstance(amount, Decimal):
            raise TypeError(
                f"amount must be Decimal, got {type(amount).__name__}. "
                f"Use Decimal(str(value)) to convert."
            )
        self.posting_id = posting_id or str(uuid4())
        self.amount = amount
        self.account_id = account_id
        self.posting_date = posting_date
        self.category_id = category_id
        self.posting_type = posting_type
        self.payee = payee
        self.description = description

    def __repr__(self) -> str:
        return (
            f"Posting({self.posting_id!r}, {self.account_id!r}, {self.amount!r}, "
            f"{self.posting_date!r}, {self.category_id!r}, {self.posting_type!r})"
        )

    def __eq__(self, other):
        if not isinstance(other, Posting):
            return False
        else:
            return self.posting_id == other.posting_id

    def __hash__(self):
        return hash(self.posting_id)

    def __lt__(self, other: Posting):
        return self.posting_date < other.posting_date


class Account:
    def __init__(
        self,
        account_id: str | None,
        name: str,
        currency: str,
        initial_balance: Decimal = Decimal(0),
        is_savings: bool = False,
    ):
        if not isinstance(initial_balance, Decimal):
            raise TypeError(
                f"initial_balance must be Decimal, "
                f"got {type(initial_balance).__name__}. "
                f"Use Decimal(str(value)) to convert."
            )
        self.account_id = account_id or str(uuid4())
        self.name = name
        if currency not in VALID_CURRENCIES:
            raise InvalidCurrencyError(f"Invalid currency: {currency}")
        self.currency = currency
        self.initial_balance = initial_balance
        self.is_savings = is_savings
        self._postings: list[Posting] = []
        self._outgoing_transfers: list[Transfer] = []
        self._incoming_transfers: list[Transfer] = []

    @property
    def balance(self) -> Decimal:
        posting_sum = sum(p.amount for p in self._postings)
        outgoing_sum = sum(t.debit_amount for t in self._outgoing_transfers)
        incoming_sum = sum(t.credit_amount for t in self._incoming_transfers)
        return self.initial_balance + posting_sum - outgoing_sum + incoming_sum

    def __repr__(self) -> str:
        return f"Account({self.account_id!r}, {self.name!r}, {self.currency!r}, {self.balance})"

    def __eq__(self, other):
        if not isinstance(other, Account):
            return False
        else:
            return self.account_id == other.account_id

    def __hash__(self):
        return hash(self.account_id)

    def record_posting(
        self,
        amount: Decimal,
        posting_date: date,
        *,
        category_id: str | None,
        posting_type: PostingType,
        payee: str | None = None,
        description: str | None = None,
    ) -> Posting:
        """Record an income or expense posting on this account.

        Args:
            amount: The posting amount. The absolute value is used and
                the sign is applied automatically based on posting_type.
            posting_date: The posting date
            category_id: Optional category ID
            posting_type: "EXPENSE" or "INCOME"

        Returns:
            The created Posting with properly signed amount:
            - EXPENSE: amount becomes negative
            - INCOME: amount becomes positive
        """
        if not isinstance(amount, Decimal):
            raise TypeError(
                f"amount must be Decimal, got {type(amount).__name__}. "
                f"Use Decimal(str(value)) to convert."
            )
        # Apply sign based on category_type
        if posting_type == PostingType.EXPENSE:
            effective_amount = -abs(amount)
        else:
            # INCOME
            effective_amount = abs(amount)

        # Check if posting would result in negative balance
        new_balance = self.balance + effective_amount
        if new_balance < 0:
            raise InsufficientFundsError(
                f"Insufficient funds in account '{self.name}' (id={self.account_id}): "
                f"current balance {self.balance} {self.currency}, "
                f"attempted posting {effective_amount} {self.currency}, "
                f"would result in balance {new_balance} {self.currency}"
            )

        posting = Posting(
            None,
            self.account_id,
            effective_amount,
            posting_date,
            category_id,
            posting_type,
            payee,
            description,
        )
        self._postings.append(posting)
        return posting

    def record_outgoing_transfer(self, transfer: Transfer) -> None:
        """Register an outgoing transfer and validate sufficient funds."""
        self._outgoing_transfers.append(transfer)
        if self.balance < 0:
            self._outgoing_transfers.remove(transfer)
            raise InsufficientFundsError(
                f"Insufficient funds in account '{self.name}' (id={self.account_id}): "
                f"transfer of {transfer.debit_amount} {self.currency} "
                f"would result in negative balance"
            )

    def record_incoming_transfer(self, transfer: Transfer) -> None:
        """Register an incoming transfer."""
        self._incoming_transfers.append(transfer)

    @property
    def postings(self) -> list[Posting]:
        return list(self._postings)

    def get_posting(self, posting_id: str) -> Posting | None:
        return next((p for p in self._postings if p.posting_id == posting_id), None)

    @property
    def has_postings(self) -> bool:
        return len(self._postings) > 0

    @property
    def has_transfers(self) -> bool:
        return len(self._outgoing_transfers) > 0 or len(self._incoming_transfers) > 0

    @property
    def posting_count(self) -> int:
        return len(self._postings)

    @property
    def transfer_count(self) -> int:
        return len(self._outgoing_transfers) + len(self._incoming_transfers)
