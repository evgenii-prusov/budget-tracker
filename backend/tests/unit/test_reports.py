import pytest
from datetime import date
from decimal import Decimal
from typing import Any

from app.service_layer.reports import (
    _compute_period_dates,
    _previous_month_range,
    _build_cumulative,
    get_spending_report,
    get_income_vs_spending,
    get_spending_timeline,
    SpendingReport,
    CategorySpendingRow,
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

    def test_period_dates_quarter_q1(self):
        start, end = _compute_period_dates("quarter", date(2026, 1, 15))
        assert start == date(2026, 1, 1)
        assert end == date(2026, 3, 31)

    def test_period_dates_quarter_q2(self):
        start, end = _compute_period_dates("quarter", date(2026, 5, 10))
        assert start == date(2026, 4, 1)
        assert end == date(2026, 6, 30)

    def test_period_dates_quarter_q3(self):
        start, end = _compute_period_dates("quarter", date(2026, 8, 1))
        assert start == date(2026, 7, 1)
        assert end == date(2026, 9, 30)

    def test_period_dates_quarter_q4(self):
        start, end = _compute_period_dates("quarter", date(2026, 12, 25))
        assert start == date(2026, 10, 1)
        assert end == date(2026, 12, 31)

    def test_invalid_period_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid period"):
            _compute_period_dates("biweekly", date(2026, 1, 1))


class TestPreviousMonthRange:
    def test_march_to_february(self):
        start, end = _previous_month_range(date(2026, 3, 15))
        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 28)

    def test_january_wraps_to_december(self):
        start, end = _previous_month_range(date(2026, 1, 15))
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_february_leap_year(self):
        start, end = _previous_month_range(date(2024, 3, 1))
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)


class TestPreviousPeriodRange:
    def test_month_delegates_to_previous_month_range(self):
        from app.service_layer.reports import _previous_period_range

        start, end = _previous_period_range("month", date(2026, 3, 15))
        expected_start, expected_end = _previous_month_range(date(2026, 3, 15))
        assert start == expected_start
        assert end == expected_end

    def test_quarter_q2_gives_q1(self):
        from app.service_layer.reports import _previous_period_range

        start, end = _previous_period_range("quarter", date(2026, 5, 15))
        assert start == date(2026, 1, 1)
        assert end == date(2026, 3, 31)

    def test_quarter_q1_wraps_to_q4_previous_year(self):
        from app.service_layer.reports import _previous_period_range

        start, end = _previous_period_range("quarter", date(2026, 2, 15))
        assert start == date(2025, 10, 1)
        assert end == date(2025, 12, 31)

    def test_year_gives_previous_year(self):
        from app.service_layer.reports import _previous_period_range

        start, end = _previous_period_range("year", date(2026, 6, 1))
        assert start == date(2025, 1, 1)
        assert end == date(2025, 12, 31)

    def test_invalid_period_raises(self):
        from app.service_layer.reports import _previous_period_range

        with pytest.raises(ValueError, match="Invalid period"):
            _previous_period_range("biweekly", date(2026, 3, 15))


class TestBuildCumulative:
    def test_accumulates_running_total(self):
        rows = [
            (date(2026, 3, 1), Decimal("10")),
            (date(2026, 3, 5), Decimal("20")),
            (date(2026, 3, 10), Decimal("30")),
        ]
        result = _build_cumulative(rows)
        assert len(result) == 3
        assert result[0].cumulative_total == Decimal("10")
        assert result[1].cumulative_total == Decimal("30")
        assert result[2].cumulative_total == Decimal("60")

    def test_empty_returns_empty(self):
        assert _build_cumulative([]) == []


class SpyReportRepository(AbstractReportRepository):
    called_with: Any

    def __init__(self, rows=None, *, income_spending_data=None, daily_spending_data=None):
        self._rows = rows or []
        self.called_with = None
        self._income_spending_data = income_spending_data or (Decimal(0), Decimal(0))
        self._daily_spending_data = daily_spending_data or []
        self.income_vs_spending_calls: list[tuple] = []
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

    def income_vs_spending(
        self, start_date: date, end_date: date, currency: str, exclude_savings: bool = True
    ) -> tuple[Decimal, Decimal]:
        self.income_vs_spending_calls.append((start_date, end_date, currency, exclude_savings))
        return self._income_spending_data

    def daily_spending(
        self, start_date: date, end_date: date, currency: str, exclude_savings: bool = True
    ) -> list[tuple[date, Decimal]]:
        self.daily_spending_calls.append((start_date, end_date, currency, exclude_savings))
        return self._daily_spending_data


class FakeUnitOfWorkWithReports(FakeUnitOfWork):
    reports: SpyReportRepository

    def __init__(self, rows=None, **kwargs):
        super().__init__()
        self.reports = SpyReportRepository(rows, **kwargs)


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

    def test_get_spending_report_quarter_period(self):
        uow = FakeUnitOfWorkWithReports()

        get_spending_report(uow, period="quarter", reference_date=date(2026, 5, 10))

        assert uow.reports.called_with[0] == date(2026, 4, 1)
        assert uow.reports.called_with[1] == date(2026, 6, 30)

    def test_get_spending_report_invalid_period_raises(self):
        uow = FakeUnitOfWorkWithReports()

        with pytest.raises(ValueError, match="Invalid period"):
            get_spending_report(uow, period="biweekly", reference_date=date(2026, 3, 1))


class TestIncomeVsSpending:
    def test_delegates_to_repo(self):
        uow = FakeUnitOfWorkWithReports(income_spending_data=(Decimal("1000"), Decimal("600")))
        result = get_income_vs_spending(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert result.currency == "EUR"
        assert result.start_date == date(2026, 3, 1)
        assert result.end_date == date(2026, 3, 31)
        # Current month call
        call = uow.reports.income_vs_spending_calls[0]
        assert call == (date(2026, 3, 1), date(2026, 3, 31), "EUR", True)

    def test_computes_net_income(self):
        uow = FakeUnitOfWorkWithReports(income_spending_data=(Decimal("1000"), Decimal("600")))
        result = get_income_vs_spending(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert result.total_income == Decimal("1000")
        assert result.total_spending == Decimal("600")
        assert result.net_income == Decimal("400")

    def test_fetches_previous_period(self):
        uow = FakeUnitOfWorkWithReports(income_spending_data=(Decimal("500"), Decimal("300")))
        result = get_income_vs_spending(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert len(uow.reports.income_vs_spending_calls) == 2
        # Second call is previous month (February)
        prev_call = uow.reports.income_vs_spending_calls[1]
        assert prev_call[0] == date(2026, 2, 1)
        assert prev_call[1] == date(2026, 2, 28)
        assert result.prev_total_income == Decimal("500")
        assert result.prev_total_spending == Decimal("300")

    def test_january_wraps_to_december(self):
        uow = FakeUnitOfWorkWithReports(income_spending_data=(Decimal("0"), Decimal("0")))
        get_income_vs_spending(uow, currency="EUR", reference_date=date(2026, 1, 15))

        prev_call = uow.reports.income_vs_spending_calls[1]
        assert prev_call[0] == date(2025, 12, 1)
        assert prev_call[1] == date(2025, 12, 31)

    def test_quarter_period_uses_quarter_dates(self):
        uow = FakeUnitOfWorkWithReports(income_spending_data=(Decimal("0"), Decimal("0")))
        result = get_income_vs_spending(
            uow, currency="EUR", period="quarter", reference_date=date(2026, 5, 15)
        )

        assert result.start_date == date(2026, 4, 1)
        assert result.end_date == date(2026, 6, 30)
        # Current period call
        curr_call = uow.reports.income_vs_spending_calls[0]
        assert curr_call[0] == date(2026, 4, 1)
        assert curr_call[1] == date(2026, 6, 30)
        # Previous period call (Q1)
        prev_call = uow.reports.income_vs_spending_calls[1]
        assert prev_call[0] == date(2026, 1, 1)
        assert prev_call[1] == date(2026, 3, 31)

    def test_year_period_uses_year_dates(self):
        uow = FakeUnitOfWorkWithReports(income_spending_data=(Decimal("0"), Decimal("0")))
        result = get_income_vs_spending(
            uow, currency="EUR", period="year", reference_date=date(2026, 6, 1)
        )

        assert result.start_date == date(2026, 1, 1)
        assert result.end_date == date(2026, 12, 31)
        # Previous period call (2025)
        prev_call = uow.reports.income_vs_spending_calls[1]
        assert prev_call[0] == date(2025, 1, 1)
        assert prev_call[1] == date(2025, 12, 31)


class TestSpendingTimeline:
    def test_delegates_to_repo(self):
        uow = FakeUnitOfWorkWithReports()
        get_spending_timeline(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert len(uow.reports.daily_spending_calls) == 2
        curr_call = uow.reports.daily_spending_calls[0]
        assert curr_call == (date(2026, 3, 1), date(2026, 3, 31), "EUR", True)

    def test_computes_cumulative_totals(self):
        uow = FakeUnitOfWorkWithReports(
            daily_spending_data=[
                (date(2026, 3, 1), Decimal("10")),
                (date(2026, 3, 2), Decimal("20")),
                (date(2026, 3, 3), Decimal("30")),
            ]
        )
        result = get_spending_timeline(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert len(result.current_period) == 3
        assert result.current_period[0].cumulative_total == Decimal("10")
        assert result.current_period[1].cumulative_total == Decimal("30")
        assert result.current_period[2].cumulative_total == Decimal("60")

    def test_fetches_both_periods(self):
        uow = FakeUnitOfWorkWithReports()
        get_spending_timeline(uow, currency="EUR", reference_date=date(2026, 3, 15))

        prev_call = uow.reports.daily_spending_calls[1]
        assert prev_call[0] == date(2026, 2, 1)
        assert prev_call[1] == date(2026, 2, 28)

    def test_empty_data(self):
        uow = FakeUnitOfWorkWithReports()
        result = get_spending_timeline(uow, currency="EUR", reference_date=date(2026, 3, 15))

        assert result.current_period == []
        assert result.previous_period == []
        assert result.currency == "EUR"

    def test_quarter_period_uses_quarter_dates(self):
        uow = FakeUnitOfWorkWithReports()
        result = get_spending_timeline(
            uow, currency="EUR", period="quarter", reference_date=date(2026, 5, 15)
        )

        assert result.start_date == date(2026, 4, 1)
        assert result.end_date == date(2026, 6, 30)
        curr_call = uow.reports.daily_spending_calls[0]
        assert curr_call[0] == date(2026, 4, 1)
        assert curr_call[1] == date(2026, 6, 30)
        # Previous quarter (Q1)
        prev_call = uow.reports.daily_spending_calls[1]
        assert prev_call[0] == date(2026, 1, 1)
        assert prev_call[1] == date(2026, 3, 31)

    def test_year_period_uses_year_dates(self):
        uow = FakeUnitOfWorkWithReports()
        result = get_spending_timeline(
            uow, currency="EUR", period="year", reference_date=date(2026, 6, 1)
        )

        assert result.start_date == date(2026, 1, 1)
        assert result.end_date == date(2026, 12, 31)
        prev_call = uow.reports.daily_spending_calls[1]
        assert prev_call[0] == date(2025, 1, 1)
        assert prev_call[1] == date(2025, 12, 31)
