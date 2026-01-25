import abc

from app.domain.model import Account
from app.domain.model import Transfer


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, account: Account):
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, account_id) -> Account:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_by_name(self, name: str) -> Account | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_all(self) -> list[Account]:
        raise NotImplementedError()

    @abc.abstractmethod
    def commit(self):
        """Persist all pending changes."""
        raise NotImplementedError()

    @abc.abstractmethod
    def rollback(self):
        """Discard all pending changes."""
        raise NotImplementedError()

    @abc.abstractmethod
    def add_transfer(self, transfer: Transfer):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transfer(self, transfer_id: str) -> Transfer:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_transfers_for_account(self, account_id: str) -> list[Transfer]:
        raise NotImplementedError()
