from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends

from app.api.dependencies import get_unit_of_work
from app.api.schemas import CategorySpendingResponse, SpendingReportResponse
from app.service_layer.reports import get_spending_report
from app.service_layer.unit_of_work import AbstractUnitOfWork

router = APIRouter()
UoWDep = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]


@router.get("/reports/spending", response_model=SpendingReportResponse)
def spending_report(
    uow: UoWDep,
    period: Literal["week", "month", "year"],
    exclude_savings: bool = True,
    reference_date: date | None = None,
) -> SpendingReportResponse:
    report = get_spending_report(
        uow,
        period=period,
        exclude_savings=exclude_savings,
        reference_date=reference_date,
    )
    return SpendingReportResponse(
        period=period,
        start_date=report.start_date,
        end_date=report.end_date,
        rows=[
            CategorySpendingResponse(
                parent_category_id=row.parent_category_id,
                parent_category_name=row.parent_category_name,
                currency=row.currency,
                total=row.total,
            )
            for row in report.rows
        ],
    )
