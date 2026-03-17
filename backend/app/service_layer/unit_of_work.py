import abc

from app.service_layer.abstract_account_repository import AbstractAccountRepository
from app.service_layer.abstract_transfer_repository import AbstractTransferRepository
from app.service_layer.abstract_category_repository import AbstractCategoryRepository
from app.service_layer.abstract_report_repository import AbstractReportRepository
from app.service_layer.abstract_settings_repository import AbstractSettingsRepository


class AbstractUnitOfWork(abc.ABC):
    accounts: AbstractAccountRepository
    transfers: AbstractTransferRepository
    categories: AbstractCategoryRepository
    reports: AbstractReportRepository
    settings: AbstractSettingsRepository

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
