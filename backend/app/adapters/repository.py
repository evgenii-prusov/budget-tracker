from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.domain.model import Account, Transfer, Category, Posting
from app.adapters.orm import accounts, categories, postings, transfers
from app.service_layer.abstract_repository import AbstractRepository


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account):
        self.session.add(account)

    def get(self, account_id: str) -> Account | None:
        return (
            self.session.execute(select(Account).filter_by(account_id=account_id))
            .scalars()
            .one_or_none()
        )

    def get_by_name(self, name: str) -> Account | None:
        return self.session.execute(select(Account).filter_by(name=name)).scalars().first()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Account]:
        return list(
            self.session.execute(
                select(Account)
                .order_by(accounts.c.name, accounts.c.account_id)
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def delete(self, account: Account) -> None:
        self.session.delete(account)

    def add_transfer(self, transfer: Transfer):
        self.session.add(transfer)

    def get_transfer(self, transfer_id: str) -> Transfer | None:
        return (
            self.session.execute(select(Transfer).filter_by(transfer_id=transfer_id))
            .scalars()
            .one_or_none()
        )

    def _transfer_filter(self, account_id: str):
        return or_(
            transfers.c.source_account_id == account_id,
            transfers.c.dest_account_id == account_id,
        )

    def list_transfers_for_account(self, account_id: str) -> list[Transfer]:
        return list(
            self.session.execute(select(Transfer).where(self._transfer_filter(account_id)))
            .scalars()
            .all()
        )

    def count_transfers_for_account(self, account_id: str) -> int:
        return self.session.execute(
            select(func.count(transfers.c.transfer_id)).where(self._transfer_filter(account_id))
        ).scalar_one()

    def list_transfers(self, skip: int = 0, limit: int = 50) -> list[Transfer]:
        return list(
            self.session.execute(
                select(Transfer)
                .order_by(transfers.c.transfer_date, transfers.c.transfer_id)
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def get_posting(self, posting_id: str) -> Posting | None:
        return (
            self.session.execute(select(Posting).filter_by(posting_id=posting_id))
            .scalars()
            .one_or_none()
        )

    def list_postings(
        self, account_id: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[Posting]:
        stmt = select(Posting)
        if account_id is not None:
            stmt = stmt.where(postings.c.account_id == account_id)
        return list(
            self.session.execute(
                stmt.order_by(postings.c.posting_date, postings.c.posting_id)
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def count_postings_for_account(self, account_id: str) -> int:
        return self.session.execute(
            select(func.count(postings.c.posting_id)).where(postings.c.account_id == account_id)
        ).scalar_one()

    # Category methods
    def add_category(self, category: Category):
        self.session.add(category)

    def get_category(self, category_id: str) -> Category | None:
        return (
            self.session.execute(select(Category).filter_by(category_id=category_id))
            .scalars()
            .one_or_none()
        )

    def get_category_by_name(self, name: str) -> Category | None:
        return self.session.execute(select(Category).filter_by(name=name)).scalars().first()

    def list_categories(self, skip: int = 0, limit: int = 50) -> list[Category]:
        return list(
            self.session.execute(
                select(Category)
                .order_by(categories.c.name, categories.c.category_id)
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def delete_category(self, category: Category) -> None:
        self.session.delete(category)

    def count_postings_for_category(self, category_id: str) -> int:
        return self.session.execute(
            select(func.count(postings.c.posting_id)).where(postings.c.category_id == category_id)
        ).scalar_one()
