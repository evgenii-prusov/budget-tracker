from decimal import Decimal
from uuid import uuid4
from datetime import date


class Transaction:
    """Represents a financial transaction on an account.

    The amount is stored as-is (positive or negative). The caller is
    responsible for ensuring the amount has the correct sign based on
    the category_type. Use Account.record_transaction() to automatically
    apply sign logic.
    """

    def __init__(
        self,
        id: str | None,
        account_id: str,
        amount: Decimal,
        date: date,
        category: str | None,
        category_type: str | None,
    ):
        self.id = id or str(uuid4())
        self.amount = (
            amount if isinstance(amount, Decimal) else Decimal(str(amount))
        )
        self.account_id = account_id
        self.date = date
        self.category = category
        self.category_type = category_type

    def __repr__(self) -> str:
        return (
            f"Transaction({self.id!r}, {self.account_id!r}, {self.amount!r}, "
            f"{self.date!r}, {self.category!r}, {self.category_type!r})"
        )

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return False
        else:
            return self.account_id == other.account_id

    def __hash__(self):
        return hash(self.account_id)

    def __gt__(self, other: Transaction):
        return self.date > other.date


class Account:
    def __init__(
        self,
        id: str | None,
        name: str,
        currency: str,
        initial_balance: Decimal = Decimal(0),
    ):
        self.id = id or str(uuid4())
        self.name = name
        self.currency = currency
        if isinstance(initial_balance, Decimal):
            self._initial_balance = initial_balance
        else:
            self._initial_balance = Decimal(str(initial_balance))
        self._transactions: list[Transaction] = []

    # TODO: implement __eq__ and __hash__ magic methods

    @property
    def balance(self) -> Decimal:
        return self._initial_balance + sum(
            tx.amount for tx in self._transactions
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

    def record_transaction(
        self,
        amount: Decimal,
        date: date,
        category: str | None = None,
        category_type: str | None = None,
    ) -> Transaction:
        """Record a transaction on this account.

        Args:
            amount: The transaction amount. For EXPENSE and INCOME, the
                absolute value is used and the sign is applied automatically.
                For TRANSFER (or when category_type is None), the caller is
                responsible for providing a correctly signed amount (negative
                for debits, positive for credits); the value is preserved
                without modification.
            date: The transaction date
            category: Optional category label
            category_type: Transaction type - "EXPENSE", "INCOME", or
                "TRANSFER"

        Returns:
            The created Transaction with properly signed amount:
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

        tx: Transaction = Transaction(
            None,
            self.id,
            effective_amount,
            date,
            category,
            category_type,
        )
        self._transactions.append(tx)
        return tx


def transfer(
    src: Account,
    dst: Account,
    date: date,
    *,
    debit_amt: Decimal,
    credit_amt: Decimal,
) -> tuple[Transaction, Transaction]:
    """Transfer funds between two accounts.

    Creates two TRANSFER transactions: one debiting the source account
    and one crediting the destination account. Supports different currencies
    by allowing different debit and credit amounts.

    Args:
        src: Source account to debit from
        dst: Destination account to credit to
        date: Date of the transfer
        debit_amt: Amount to deduct from source (must be positive). This
            value is negated internally when recording the debit transaction.
        credit_amt: Amount to add to destination (must be positive)

    Returns:
        Tuple of (debit_transaction, credit_transaction)

    Raises:
        ValueError: If either amount is not positive

    Note:
        Both parameters expect positive values for user convenience.
        The debit_amt is negated when passed to record_transaction()
        because TRANSFER transactions use amounts as-is, and debits
        must be negative to decrease the source account balance.
    """
    if debit_amt <= 0 or credit_amt <= 0:
        raise ValueError("Amounts must be greater than zero")

    # Negate debit_amt because TRANSFER transactions use amounts as-is,
    # and debits must be negative to decrease the source account balance
    debit_tx = src.record_transaction(
        -debit_amt, date, category_type="TRANSFER"
    )
    credit_tx = dst.record_transaction(
        credit_amt, date, category_type="TRANSFER"
    )

    return debit_tx, credit_tx
