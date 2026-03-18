from datetime import date
from decimal import Decimal

from sqlalchemy import case, select, func, literal
from sqlalchemy.orm import Session

from app.adapters.orm import accounts, postings, categories
from app.service_layer.abstract_report_repository import AbstractReportRepository
from app.service_layer.reports import CategorySpendingRow, SpendingReport


class SqlAlchemyReportRepository(AbstractReportRepository):
    def __init__(self, session: Session):
        self._session = session

    def spending_by_period(
        self,
        start_date: date,
        end_date: date,
        exclude_savings: bool = True,
    ) -> SpendingReport:
        # Alias categories table for the parent join
        pc = categories.alias("pc")

        stmt = (
            select(
                func.coalesce(pc.c.category_id, categories.c.category_id).label(
                    "parent_category_id"
                ),
                func.coalesce(pc.c.name, categories.c.name).label("parent_category_name"),
                accounts.c.currency,
                func.sum(func.abs(postings.c.amount)).label("total"),
            )
            .select_from(postings)
            .join(accounts, postings.c.account_id == accounts.c.account_id)
            .join(categories, postings.c.category_id == categories.c.category_id)
            .outerjoin(pc, categories.c.parent_id == pc.c.category_id)
            .where(postings.c.posting_type == "EXPENSE")
            .where(postings.c.posting_date.between(start_date, end_date))
            .group_by(
                func.coalesce(pc.c.category_id, categories.c.category_id),
                func.coalesce(pc.c.name, categories.c.name),
                accounts.c.currency,
            )
            .order_by(
                func.coalesce(pc.c.name, categories.c.name),
                accounts.c.currency,
            )
        )
        if exclude_savings:
            stmt = stmt.where(accounts.c.is_savings.is_(False))

        rows = [
            CategorySpendingRow(
                parent_category_id=row.parent_category_id,
                parent_category_name=row.parent_category_name,
                currency=row.currency,
                total=Decimal(str(row.total)),
            )
            for row in self._session.execute(stmt)
        ]

        return SpendingReport(
            period="",  # filled in by service layer
            start_date=start_date,
            end_date=end_date,
            rows=rows,
        )

    def income_vs_spending(
        self,
        start_date: date,
        end_date: date,
        currency: str,
        exclude_savings: bool = True,
    ) -> tuple[Decimal, Decimal]:
        stmt = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (postings.c.posting_type == "INCOME", func.abs(postings.c.amount)),
                            else_=literal(0),
                        )
                    ),
                    0,
                ).label("total_income"),
                func.coalesce(
                    func.sum(
                        case(
                            (postings.c.posting_type == "EXPENSE", func.abs(postings.c.amount)),
                            else_=literal(0),
                        )
                    ),
                    0,
                ).label("total_spending"),
            )
            .select_from(postings)
            .join(accounts, postings.c.account_id == accounts.c.account_id)
            .where(postings.c.posting_date.between(start_date, end_date))
            .where(accounts.c.currency == currency)
        )
        if exclude_savings:
            stmt = stmt.where(accounts.c.is_savings.is_(False))
        row = self._session.execute(stmt).one()
        return Decimal(str(row.total_income)), Decimal(str(row.total_spending))

    def daily_spending(
        self,
        start_date: date,
        end_date: date,
        currency: str,
        exclude_savings: bool = True,
    ) -> list[tuple[date, Decimal]]:
        stmt = (
            select(
                postings.c.posting_date,
                func.sum(func.abs(postings.c.amount)).label("daily_total"),
            )
            .select_from(postings)
            .join(accounts, postings.c.account_id == accounts.c.account_id)
            .where(postings.c.posting_type == "EXPENSE")
            .where(postings.c.posting_date.between(start_date, end_date))
            .where(accounts.c.currency == currency)
            .group_by(postings.c.posting_date)
            .order_by(postings.c.posting_date)
        )
        if exclude_savings:
            stmt = stmt.where(accounts.c.is_savings.is_(False))
        return [
            (row.posting_date, Decimal(str(row.daily_total))) for row in self._session.execute(stmt)
        ]
