import abc

from app.domain.model import Account
from app.domain.model import Transfer
from app.domain.model import Category
from app.domain.model import Posting


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, account: Account):
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, account_id: str) -> Account | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_by_name(self, name: str) -> Account | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_all(self, skip: int = 0, limit: int = 100) -> list[Account]:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete(self, account: Account) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def add_transfer(self, transfer: Transfer):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transfer(self, transfer_id: str) -> Transfer | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_transfers_for_account(self, account_id: str) -> list[Transfer]:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_transfers(self, skip: int = 0, limit: int = 100) -> list[Transfer]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_posting(self, posting_id: str) -> Posting | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_postings(
        self, account_id: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[Posting]:
        raise NotImplementedError()

    # Category methods
    @abc.abstractmethod
    def add_category(self, category: Category):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_category(self, category_id: str) -> Category | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_category_by_name(self, name: str) -> Category | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_categories(self, skip: int = 0, limit: int = 100) -> list[Category]:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_category(self, category: Category) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def count_postings_for_category(self, category_id: str) -> int:
        raise NotImplementedError()
