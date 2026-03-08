from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal


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


def get_spending_report(
    uow,
    *,
    period: str,
    exclude_savings: bool = True,
    reference_date: date | None = None,
) -> SpendingReport:
    ref = reference_date or date.today()
    start, end = _compute_period_dates(period, ref)
    with uow:
        return uow.reports.spending_by_period(start, end, exclude_savings=exclude_savings)
