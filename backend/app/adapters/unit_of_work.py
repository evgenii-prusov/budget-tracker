from sqlalchemy.orm import Session

from app.adapters.account_repository import SqlAlchemyAccountRepository
from app.adapters.transfer_repository import SqlAlchemyTransferRepository
from app.adapters.category_repository import SqlAlchemyCategoryRepository
from app.adapters.report_repository import SqlAlchemyReportRepository
from app.adapters.settings_repository import SqlAlchemySettingsRepository
from app.service_layer.unit_of_work import AbstractUnitOfWork


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session: Session):
        self.accounts = SqlAlchemyAccountRepository(session)
        self.transfers = SqlAlchemyTransferRepository(session)
        self.categories = SqlAlchemyCategoryRepository(session)
        self.reports = SqlAlchemyReportRepository(session)
        self.settings = SqlAlchemySettingsRepository(session)
        self._session = session

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()
