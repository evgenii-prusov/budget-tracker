import abc

from app.domain.model import Category


class AbstractCategoryRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, category: Category) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, category_id: str) -> Category | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_by_name(self, name: str, parent_id: str | None = None) -> Category | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_all(self, skip: int = 0, limit: int = 50) -> list[Category]:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_parents(self, skip: int = 0, limit: int = 50) -> list[Category]:
        raise NotImplementedError()

    @abc.abstractmethod
    def list_children(self, parent_id: str) -> list[Category]:
        raise NotImplementedError()

    @abc.abstractmethod
    def count_children(self, category_id: str) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete(self, category: Category) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def count_postings(self, category_id: str) -> int:
        raise NotImplementedError()
