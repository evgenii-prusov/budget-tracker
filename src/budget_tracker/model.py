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
import functools


class InsufficientFundsError(Exception):
    """Raised when an operation would result in a negative account balance."""

    pass


@functools.total_ordering
class Entry:
    """Represents a financial entry on an account.

    The amount is stored as-is (positive or negative). The caller is
    responsible for ensuring the amount has the correct sign based on
    the category_type. Use Account.record_entry() to automatically
    apply sign logic.
    """

    def __init__(
        self,
        id: str | None,
        account_id: str,
        amount: Decimal,
        date: date,
        category: str,
        category_type: str,
    ):
        if not isinstance(amount, Decimal):
            raise TypeError(
                f"amount must be Decimal, got {type(amount).__name__}. "
                f"Use Decimal(str(value)) to convert."
            )
        self.id = id or str(uuid4())
        self.amount = amount
        self.account_id = account_id
        self.date = date
        self.category = category
        self.category_type = category_type

    def __repr__(self) -> str:
        return (
            f"Entry({self.id!r}, {self.account_id!r}, {self.amount!r}, "
            f"{self.date!r}, {self.category!r}, {self.category_type!r})"
        )

    def __eq__(self, other):
        if not isinstance(other, Entry):
            return False
        else:
            return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __lt__(self, other: Entry):
        return self.date < other.date


class Account:
    def __init__(
        self,
        id: str | None,
        name: str,
        currency: str,
        initial_balance: Decimal = Decimal("0"),
    ):
        if not isinstance(initial_balance, Decimal):
            raise TypeError(
                f"initial_balance must be Decimal, "
                f"got {type(initial_balance).__name__}. "
                f"Use Decimal(str(value)) to convert."
            )
        self.id = id or str(uuid4())
        self.name = name
        self.currency = currency
        self.initial_balance = initial_balance
        self._entries: list[Entry] = []

    @property
    def balance(self) -> Decimal:
        return self.initial_balance + sum(
            entry.amount for entry in self._entries
        )

    def __repr__(self) -> str:
        return (
            f"Account({self.id!r}, {self.name!r}, {self.currency!r}, "
            f"{self.balance})"
        )

    def __eq__(self, other):
        if not isinstance(other, Account):
            return False
        else:
            return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def record_entry(
        self,
        amount: Decimal,
        date: date,
        category: str,
        category_type: str,
    ) -> Entry:
        """Record an entry on this account.

        Args:
            amount: The entry amount. For EXPENSE and INCOME, the
                absolute value is used and the sign is applied automatically.
                For TRANSFER (or when category_type is None), the caller is
                responsible for providing a correctly signed amount (negative
                for debits, positive for credits); the value is preserved
                without modification.
            date: The entry date
            category: Optional category label
            category_type: Entry type - "EXPENSE", "INCOME", or
                "TRANSFER"

        Returns:
            The created Entry with properly signed amount:
            - EXPENSE: amount becomes negative
            - INCOME: amount becomes positive
            - TRANSFER or None: amount preserved as provided (caller must
              ensure correct sign)
        """
        # Apply sign based on category_type
        if category_type == "EXPENSE":
            effective_amount = -abs(amount)
        elif category_type == "INCOME":
            effective_amount = abs(amount)
        else:
            # TRANSFER or None - preserve caller-provided amount
            effective_amount = amount

        # Check if entry would result in negative balance
        new_balance = self.balance + effective_amount
        if new_balance < 0:
            raise InsufficientFundsError(
                f"Insufficient funds in account '{self.name}' (id={self.id}): "
                f"current balance {self.balance} {self.currency}, "
                f"attempted entry {effective_amount} {self.currency}, "
                f"would result in balance {new_balance} {self.currency}"
            )

        entry: Entry = Entry(
            None,
            self.id,
            effective_amount,
            date,
            category,
            category_type,
        )
        self._entries.append(entry)
        return entry


def transfer(
    src: Account,
    dst: Account,
    date: date,
    *,
    debit_amt: Decimal,
    credit_amt: Decimal,
) -> tuple[Entry, Entry]:
    """Transfer funds between two accounts.

    Creates two TRANSFER entries: one debiting the source account
    and one crediting the destination account. Supports different currencies
    by allowing different debit and credit amounts.

    Args:
        src: Source account to debit from
        dst: Destination account to credit to
        date: Date of the transfer
        debit_amt: Amount to deduct from source (must be positive). This
            value is negated internally when recording the debit entry.
        credit_amt: Amount to add to destination (must be positive)

    Returns:
        Tuple of (debit_entry, credit_entry)

    Raises:
        TypeError: If debit_amt or credit_amt is not a Decimal
        ValueError: If either amount is not positive

    Note:
        Both parameters expect positive values for user convenience.
        The debit_amt is negated when passed to record_entry()
        because TRANSFER entries use amounts as-is, and debits
        must be negative to decrease the source account balance.
    """
    if not isinstance(debit_amt, Decimal):
        raise TypeError(
            f"debit_amt must be Decimal, got {type(debit_amt).__name__}. "
            f"Use Decimal(str(value)) to convert."
        )
    if not isinstance(credit_amt, Decimal):
        raise TypeError(
            f"credit_amt must be Decimal, got {type(credit_amt).__name__}. "
            f"Use Decimal(str(value)) to convert."
        )
    if debit_amt <= 0 or credit_amt <= 0:
        raise ValueError("Amounts must be greater than zero")

    # Negate debit_amt because TRANSFER entries use amounts as-is,
    # and debits must be negative to decrease the source account balance
    debit_entry = src.record_entry(
        -debit_amt, date, category="TRANSFER", category_type="TRANSFER"
    )
    credit_entry = dst.record_entry(
        credit_amt, date, category="TRANSFER", category_type="TRANSFER"
    )

    return debit_entry, credit_entry
