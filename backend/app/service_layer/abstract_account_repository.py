import abc

from app.domain.model import Account


class AbstractAccountRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, account: Account) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, account_id: str) -> Account | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_by_name(self, name: str) -> Account | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_by_posting_id(self, posting_id: str) -> Account | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_all(self, skip: int = 0, limit: int = 50) -> list[Account]:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete(self, account: Account) -> None:
        raise NotImplementedError()
