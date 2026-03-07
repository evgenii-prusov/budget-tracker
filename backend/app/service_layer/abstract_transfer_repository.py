import abc

from app.domain.model import Transfer


class AbstractTransferRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, transfer: Transfer) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, transfer_id: str) -> Transfer | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_all(self, skip: int = 0, limit: int = 50) -> list[Transfer]:
        raise NotImplementedError()
