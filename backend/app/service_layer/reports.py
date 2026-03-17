from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.service_layer.unit_of_work import AbstractUnitOfWork


@dataclass
class CategorySpendingRow:
    parent_category_id: str
    parent_category_name: str
    currency: str
    total: Decimal


@dataclass
class SpendingReport:
    period: str
    start_date: date
    end_date: date
    rows: list[CategorySpendingRow]


def _compute_period_dates(period: str, reference: date) -> tuple[date, date]:
    if period == "week":
        start = reference - timedelta(days=reference.weekday())  # Monday
        return start, start + timedelta(days=6)
    elif period == "month":
        start = reference.replace(day=1)
        next_month = (start + timedelta(days=32)).replace(day=1)
        return start, next_month - timedelta(days=1)
    elif period == "year":
        return reference.replace(month=1, day=1), reference.replace(month=12, day=31)
    else:
        raise ValueError(f"Invalid period: {period!r}. Must be 'week', 'month', or 'year'")


def _previous_month_range(reference: date) -> tuple[date, date]:
    """Return (start, end) of the month preceding the month that contains reference."""
    if reference.month == 1:
        prev_year = reference.year - 1
        prev_month = 12
    else:
        prev_year = reference.year
        prev_month = reference.month - 1
    start = date(prev_year, prev_month, 1)
    next_month = (start + timedelta(days=32)).replace(day=1)
    end = next_month - timedelta(days=1)
    return start, end


@dataclass
class IncomeVsSpendingSummary:
    start_date: date
    end_date: date
    currency: str
    total_income: Decimal
    total_spending: Decimal
    net_income: Decimal
    prev_total_income: Decimal
    prev_total_spending: Decimal


@dataclass
class DailySpendingRow:
    spending_date: date
    daily_total: Decimal
    cumulative_total: Decimal


@dataclass
class SpendingTimelineReport:
    start_date: date
    end_date: date
    currency: str
    current_period: list[DailySpendingRow] = field(default_factory=list)
    previous_period: list[DailySpendingRow] = field(default_factory=list)


def _build_cumulative(daily_rows: list[tuple[date, Decimal]]) -> list[DailySpendingRow]:
    result: list[DailySpendingRow] = []
    running = Decimal(0)
    for spending_date, daily_total in daily_rows:
        running += daily_total
        result.append(DailySpendingRow(spending_date, daily_total, running))
    return result


def get_spending_report(
    uow: AbstractUnitOfWork,
    *,
    period: str,
    exclude_savings: bool = True,
    reference_date: date | None = None,
) -> SpendingReport:
    ref = reference_date or date.today()
    start, end = _compute_period_dates(period, ref)
    with uow:
        report = uow.reports.spending_by_period(start, end, exclude_savings=exclude_savings)
        report.period = period
        return report


def get_income_vs_spending(
    uow: AbstractUnitOfWork,
    *,
    currency: str,
    exclude_savings: bool = True,
    reference_date: date | None = None,
) -> IncomeVsSpendingSummary:
    ref = reference_date or date.today()
    start, end = _compute_period_dates("month", ref)
    prev_start, prev_end = _previous_month_range(ref)
    with uow:
        total_income, total_spending = uow.reports.income_vs_spending(
            start, end, currency, exclude_savings=exclude_savings
        )
        prev_total_income, prev_total_spending = uow.reports.income_vs_spending(
            prev_start, prev_end, currency, exclude_savings=exclude_savings
        )
    return IncomeVsSpendingSummary(
        start_date=start,
        end_date=end,
        currency=currency,
        total_income=total_income,
        total_spending=total_spending,
        net_income=total_income - total_spending,
        prev_total_income=prev_total_income,
        prev_total_spending=prev_total_spending,
    )


def get_spending_timeline(
    uow: AbstractUnitOfWork,
    *,
    currency: str,
    exclude_savings: bool = True,
    reference_date: date | None = None,
) -> SpendingTimelineReport:
    ref = reference_date or date.today()
    start, end = _compute_period_dates("month", ref)
    prev_start, prev_end = _previous_month_range(ref)
    with uow:
        current_raw = uow.reports.daily_spending(
            start, end, currency, exclude_savings=exclude_savings
        )
        prev_raw = uow.reports.daily_spending(
            prev_start, prev_end, currency, exclude_savings=exclude_savings
        )
    return SpendingTimelineReport(
        start_date=start,
        end_date=end,
        currency=currency,
        current_period=_build_cumulative(current_raw),
        previous_period=_build_cumulative(prev_raw),
    )
