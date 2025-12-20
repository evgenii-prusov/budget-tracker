from decimal import Decimal
from uuid import uuid4

class Transaction:

    def __init__(
        self,
        id: str,
        account_id: str,
        amount: Decimal
    ):
        self.id = id or str(uuid4())
        self.amount = amount if isinstance(amount, Decimal) else Decimal(str(amount))
        self.account_id = account_id

    def __repr__(self) -> str:
        return f"Transaction({self.id!r}, {self.account_id!r}, {self.amount!r})"


class Account:

    def __init__(
        self,
        id: str,
        name: str,
        currency: str,
        initial_balance: Decimal = Decimal(0)
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
        return self._initial_balance + sum(tx.amount for tx in self._transactions)

    def __repr__(self) -> str:
        return f"Account({self.id!r}, {self.name!r}, {self.currency!r}, {self.balance})"

    def record_transaction(self, amount: Decimal) -> Transaction:
        transaction: Transaction = Transaction(id=None, account_id=self.id, amount=amount)
        self._transactions.append(transaction)
        return transaction
