"""Dashboard API endpoints: Income vs Spending, Spending by Categories, Spending Timeline."""

import calendar
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_unit_of_work
from app.api.schemas import (
    CategorySpendingResponse,
    DailySpendingResponse,
    IncomeVsSpendingResponse,
    SpendingTimelineResponse,
)
from app.service_layer.reports import (
    get_income_vs_spending,
    get_spending_report,
    get_spending_timeline,
)
from app.service_layer.unit_of_work import AbstractUnitOfWork

router = APIRouter()
UoWDep = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]


def _spending_ratio(spending: Decimal, income: Decimal) -> Decimal | None:
    """spending / income * 100, None if income is zero."""
    if income == 0:
        return None
    return spending * 100 / income


@router.get("/dashboard/income-vs-spending", response_model=IncomeVsSpendingResponse)
def income_vs_spending(
    uow: UoWDep,
    currency: str,
    reference_date: date | None = None,
    exclude_savings: bool = True,
):
    summary = get_income_vs_spending(
        uow,
        currency=currency,
        exclude_savings=exclude_savings,
        reference_date=reference_date,
    )
    return IncomeVsSpendingResponse(
        start_date=summary.start_date,
        end_date=summary.end_date,
        currency=summary.currency,
        total_income=summary.total_income,
        total_spending=summary.total_spending,
        net_income=summary.net_income,
        prev_total_income=summary.prev_total_income,
        prev_total_spending=summary.prev_total_spending,
        spending_ratio=_spending_ratio(summary.total_spending, summary.total_income),
        prev_spending_ratio=_spending_ratio(summary.prev_total_spending, summary.prev_total_income),
    )


@router.get(
    "/dashboard/spending-by-categories",
    response_model=list[CategorySpendingResponse],
)
def spending_by_categories(
    uow: UoWDep,
    currency: str,
    reference_date: date | None = None,
    exclude_savings: bool = True,
):
    report = get_spending_report(
        uow,
        period="month",
        exclude_savings=exclude_savings,
        reference_date=reference_date,
    )
    return [
        CategorySpendingResponse(
            parent_category_id=row.parent_category_id,
            parent_category_name=row.parent_category_name,
            currency=row.currency,
            total=row.total,
        )
        for row in report.rows
        if row.currency == currency
    ]


@router.get("/dashboard/spending-timeline", response_model=SpendingTimelineResponse)
def spending_timeline(
    uow: UoWDep,
    currency: str,
    reference_date: date | None = None,
    exclude_savings: bool = True,
):
    ref = reference_date or date.today()
    timeline = get_spending_timeline(
        uow,
        currency=currency,
        exclude_savings=exclude_savings,
        reference_date=reference_date,
    )

    # Compute projected total
    projected_total: Decimal | None = None
    if timeline.current_period:
        cumulative = timeline.current_period[-1].cumulative_total
        days_in_month = calendar.monthrange(ref.year, ref.month)[1]
        day_of_month = ref.day
        if day_of_month > 0:
            projected_total = cumulative * days_in_month / day_of_month

    return SpendingTimelineResponse(
        start_date=timeline.start_date,
        end_date=timeline.end_date,
        currency=timeline.currency,
        current_period=[
            DailySpendingResponse(
                spending_date=row.spending_date,
                daily_total=row.daily_total,
                cumulative_total=row.cumulative_total,
            )
            for row in timeline.current_period
        ],
        previous_period=[
            DailySpendingResponse(
                spending_date=row.spending_date,
                daily_total=row.daily_total,
                cumulative_total=row.cumulative_total,
            )
            for row in timeline.previous_period
        ],
        projected_total=projected_total,
    )
