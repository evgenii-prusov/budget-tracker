import abc

from app.service_layer.abstract_account_repository import AbstractAccountRepository
from app.service_layer.abstract_transfer_repository import AbstractTransferRepository
from app.service_layer.abstract_category_repository import AbstractCategoryRepository


class AbstractUnitOfWork(abc.ABC):
    accounts: AbstractAccountRepository
    transfers: AbstractTransferRepository
    categories: AbstractCategoryRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError()
