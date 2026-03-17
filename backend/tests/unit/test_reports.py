import pytest
from datetime import date
from decimal import Decimal
from typing import Any

from app.service_layer.reports import (
    _compute_period_dates,
    get_spending_report,
    get_spending_timeline,
    SpendingReport,
    CategorySpendingRow,
    DailySpendingRow,
    SpendingTimelineReport,
)
from app.service_layer.abstract_report_repository import AbstractReportRepository
from tests.unit.test_services import FakeUnitOfWork


class TestPeriodDates:
    def test_period_dates_week_monday_start(self):
        # Wednesday 2026-03-04
        ref = date(2026, 3, 4)
        start, end = _compute_period_dates("week", ref)
        assert start == date(2026, 3, 2)  # Monday
        assert end == date(2026, 3, 8)  # Sunday

    def test_period_dates_week_monday_is_start(self):
        # If ref is already Monday
        ref = date(2026, 3, 2)
        start, end = _compute_period_dates("week", ref)
        assert start == date(2026, 3, 2)
        assert end == date(2026, 3, 8)

    def test_period_dates_week_sunday_is_end(self):
        # If ref is Sunday
        ref = date(2026, 3, 8)
        start, end = _compute_period_dates("week", ref)
        assert start == date(2026, 3, 2)
        assert end == date(2026, 3, 8)

    def test_period_dates_month_first_last(self):
        ref = date(2026, 3, 15)
        start, end = _compute_period_dates("month", ref)
        assert start == date(2026, 3, 1)
        assert end == date(2026, 3, 31)

    def test_period_dates_month_february_non_leap(self):
        ref = date(2025, 2, 10)
        start, end = _compute_period_dates("month", ref)
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_period_dates_month_february_leap(self):
        ref = date(2024, 2, 10)
        start, end = _compute_period_dates("month", ref)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_period_dates_year_jan_dec(self):
        ref = date(2026, 7, 4)
        start, end = _compute_period_dates("year", ref)
        assert start == date(2026, 1, 1)
        assert end == date(2026, 12, 31)

    def test_invalid_period_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid period"):
            _compute_period_dates("quarter", date(2026, 1, 1))


class SpyReportRepository(AbstractReportRepository):
    called_with: Any

    def __init__(self, rows=None, daily_rows=None):
        self._rows = rows or []
        self._daily_rows = daily_rows or []
        self.called_with = None
        self.daily_spending_calls: list[tuple] = []

    def spending_by_period(
        self, start_date: date, end_date: date, exclude_savings: bool = True
    ) -> SpendingReport:
        self.called_with = (start_date, end_date, exclude_savings)
        return SpendingReport(
            period="month",
            start_date=start_date,
            end_date=end_date,
            rows=self._rows,
        )

    def daily_spending(
        self,
        start_date: date,
        end_date: date,
        currency: str,
        exclude_savings: bool = True,
    ) -> list[tuple[date, Decimal]]:
        self.daily_spending_calls.append((start_date, end_date, currency, exclude_savings))
        return self._daily_rows


class FakeUnitOfWorkWithReports(FakeUnitOfWork):
    reports: SpyReportRepository

    def __init__(self, rows=None):
        super().__init__()
        self.reports = SpyReportRepository(rows)


class TestGetSpendingReport:
    def test_get_spending_report_delegates_to_repo(self):
        rows = [
            CategorySpendingRow(
                parent_category_id="cat-1",
                parent_category_name="Food",
                currency="EUR",
                total=Decimal("150.00"),
            )
        ]
        uow = FakeUnitOfWorkWithReports(rows)

        report = get_spending_report(uow, period="month", reference_date=date(2026, 3, 15))

        assert report.period == "month"
        assert report.start_date == date(2026, 3, 1)
        assert report.end_date == date(2026, 3, 31)
        assert len(report.rows) == 1
        assert report.rows[0].parent_category_name == "Food"
        assert report.rows[0].total == Decimal("150.00")

    def test_get_spending_report_passes_exclude_savings(self):
        uow = FakeUnitOfWorkWithReports()

        get_spending_report(
            uow, period="month", exclude_savings=False, reference_date=date(2026, 3, 15)
        )

        assert uow.reports.called_with[2] is False

    def test_get_spending_report_exclude_savings_defaults_true(self):
        uow = FakeUnitOfWorkWithReports()

        get_spending_report(uow, period="month", reference_date=date(2026, 3, 15))

        assert uow.reports.called_with[2] is True

    def test_get_spending_report_week_period(self):
        uow = FakeUnitOfWorkWithReports()

        get_spending_report(uow, period="week", reference_date=date(2026, 3, 4))

        # Wednesday 2026-03-04 -> week starts Monday 2026-03-02
        assert uow.reports.called_with[0] == date(2026, 3, 2)
        assert uow.reports.called_with[1] == date(2026, 3, 8)

    def test_get_spending_report_invalid_period_raises(self):
        uow = FakeUnitOfWorkWithReports()

        with pytest.raises(ValueError, match="Invalid period"):
            get_spending_report(uow, period="quarter", reference_date=date(2026, 3, 1))


class FakeUnitOfWorkWithTimeline(FakeUnitOfWork):
    reports: SpyReportRepository

    def __init__(self, daily_rows=None):
        super().__init__()
        self.reports = SpyReportRepository(daily_rows=daily_rows)


class TestSpendingTimeline:
    def test_delegates_to_repo(self):
        """get_spending_timeline calls daily_spending with correct date range and currency."""
        uow = FakeUnitOfWorkWithTimeline()

        result = get_spending_timeline(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert isinstance(result, SpendingTimelineReport)
        assert result.currency == "EUR"
        # Current period: March 2026
        assert result.start_date == date(2026, 3, 1)
        assert result.end_date == date(2026, 3, 31)

    def test_computes_cumulative_totals(self):
        """Daily totals [10, 20, 30] should produce cumulative [10, 30, 60]."""
        daily_rows = [
            (date(2026, 3, 1), Decimal("10")),
            (date(2026, 3, 2), Decimal("20")),
            (date(2026, 3, 3), Decimal("30")),
        ]
        uow = FakeUnitOfWorkWithTimeline(daily_rows=daily_rows)

        result = get_spending_timeline(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert len(result.current_period) == 3
        assert result.current_period[0] == DailySpendingRow(
            spending_date=date(2026, 3, 1),
            daily_total=Decimal("10"),
            cumulative_total=Decimal("10"),
        )
        assert result.current_period[1] == DailySpendingRow(
            spending_date=date(2026, 3, 2),
            daily_total=Decimal("20"),
            cumulative_total=Decimal("30"),
        )
        assert result.current_period[2] == DailySpendingRow(
            spending_date=date(2026, 3, 3),
            daily_total=Decimal("30"),
            cumulative_total=Decimal("60"),
        )

    def test_fetches_both_periods(self):
        """daily_spending is called twice: once for current month, once for previous month."""
        uow = FakeUnitOfWorkWithTimeline()

        get_spending_timeline(uow, currency="EUR", reference_date=date(2026, 3, 15))

        calls = uow.reports.daily_spending_calls
        assert len(calls) == 2

        # Current period: March 2026
        current_call = calls[0]
        assert current_call[0] == date(2026, 3, 1)
        assert current_call[1] == date(2026, 3, 31)
        assert current_call[2] == "EUR"

        # Previous period: February 2026
        prev_call = calls[1]
        assert prev_call[0] == date(2026, 2, 1)
        assert prev_call[1] == date(2026, 2, 28)
        assert prev_call[2] == "EUR"

    def test_fetches_both_periods_january_wraps_to_december(self):
        """When reference is January, previous month wraps to December of previous year."""
        uow = FakeUnitOfWorkWithTimeline()

        get_spending_timeline(uow, currency="USD", reference_date=date(2026, 1, 10))

        calls = uow.reports.daily_spending_calls
        assert len(calls) == 2

        prev_call = calls[1]
        assert prev_call[0] == date(2025, 12, 1)
        assert prev_call[1] == date(2025, 12, 31)

    def test_empty_data(self):
        """Empty repo returns empty current_period and previous_period lists."""
        uow = FakeUnitOfWorkWithTimeline(daily_rows=[])

        result = get_spending_timeline(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert result.current_period == []
        assert result.previous_period == []
