from decimal import Decimal
from uuid import uuid4
from datetime import date


class Transaction:
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
        _amount = (
            amount if isinstance(amount, Decimal) else Decimal(str(amount))
        )
        if category_type == "EXPENSE":
            _effective_amount: Decimal = -abs(_amount)
        elif category_type == "INCOME":
            _effective_amount: Decimal = abs(_amount)
        elif category_type == "TRANSFER":
            _effective_amount = amount

        self.amount: Decimal = _effective_amount
        self.account_id = account_id
        self.date = date
        self.category = category
        self.category_type = category_type

    def __repr__(self) -> str:
        return (
            f"Transaction({self.id!r}, {self.account_id!r}, {self.amount!r}, "
            f"{self.date!r}, {self.category!r}, {self.category_type!r})"
        )


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

    def record_transaction(
        self,
        amount: Decimal,
        date: date,
        category: str | None = None,
        category_type: str | None = None,
    ) -> Transaction:
        tx: Transaction = Transaction(
            None,
            self.id,
            amount,
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
    if debit_amt <= 0 or credit_amt <= 0:
        raise ValueError("Amounts must be positive")

    debit_tx = src.record_transaction(
        -debit_amt, date, category_type="TRANSFER"
    )
    credit_tx = dst.record_transaction(
        credit_amt, date, category_type="TRANSFER"
    )

    return debit_tx, credit_tx
