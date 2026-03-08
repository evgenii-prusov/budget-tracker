import abc
from datetime import date

from app.service_layer.reports import SpendingReport


class AbstractReportRepository(abc.ABC):
    @abc.abstractmethod
    def spending_by_period(
        self,
        start_date: date,
        end_date: date,
        exclude_savings: bool = True,
    ) -> SpendingReport:
        raise NotImplementedError()
