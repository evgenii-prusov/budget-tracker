import abc

from app.service_layer.abstract_repository import AbstractRepository


class AbstractUnitOfWork(abc.ABC):
    repo: AbstractRepository

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
