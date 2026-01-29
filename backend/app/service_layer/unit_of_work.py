import abc

from app.service_layer.abstract_repository import AbstractRepository


class AbstractUnitOfWork(abc.ABC):
    repo: AbstractRepository

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError()
