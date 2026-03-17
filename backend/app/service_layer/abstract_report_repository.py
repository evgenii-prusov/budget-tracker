import abc
from datetime import date
from decimal import Decimal

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

    @abc.abstractmethod
    def daily_spending(
        self,
        start_date: date,
        end_date: date,
        currency: str,
        exclude_savings: bool = True,
    ) -> list[tuple[date, Decimal]]:
        raise NotImplementedError()
