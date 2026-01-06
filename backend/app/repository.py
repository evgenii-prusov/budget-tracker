import abc

from sqlalchemy.orm import Session

from app.model import Account


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


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account):
        self.session.add(account)

    def get(self, account_id) -> Account:
        return self.session.query(Account).filter_by(id=account_id).one()

    def get_by_name(self, name: str) -> Account | None:
        return self.session.query(Account).filter_by(name=name).first()

    def list_all(self) -> list[Account]:
        return self.session.query(Account).all()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
