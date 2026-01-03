from ast import List

from budget_tracker.model import Account
from budget_tracker.repository import AbstractRepository


class FakeRepository(AbstractRepository):
    def __init__(self, accounts: list[Account]):
        self.accounts = accounts

    def add(self, account: Account):
        self.accounts.append(account)

    def get(self, account_id: str) -> Account:
        return next(acc for acc in self.accounts if acc.id == account_id)

    def list_all(self) -> List[Account]:
        return list(self.accounts)


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True
