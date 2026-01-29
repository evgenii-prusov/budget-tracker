from sqlalchemy.orm import Session

from app.adapters.repository import SqlAlchemyRepository
from app.service_layer.unit_of_work import AbstractUnitOfWork


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session: Session):
        self.repo = SqlAlchemyRepository(session)
        self._session = session

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()
