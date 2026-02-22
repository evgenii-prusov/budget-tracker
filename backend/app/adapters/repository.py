from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.domain.model import Account
from app.domain.model import Transfer
from app.domain.model import Category
from app.domain.model import Posting
from app.adapters.orm import accounts, categories, postings, transfers
from app.service_layer.abstract_repository import AbstractRepository


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account):
        self.session.add(account)

    def get(self, account_id: str) -> Account | None:
        return self.session.query(Account).filter_by(account_id=account_id).one_or_none()

    def get_by_name(self, name: str) -> Account | None:
        return self.session.query(Account).filter_by(name=name).first()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Account]:
        return (
            self.session.query(Account)
            .order_by(accounts.c.name, accounts.c.account_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete(self, account: Account) -> None:
        self.session.delete(account)

    def add_transfer(self, transfer: Transfer):
        self.session.add(transfer)

    def get_transfer(self, transfer_id: str) -> Transfer | None:
        return self.session.query(Transfer).filter_by(transfer_id=transfer_id).one_or_none()

    def list_transfers_for_account(self, account_id: str) -> list[Transfer]:
        return (
            self.session.query(Transfer)
            .filter(
                or_(
                    Transfer.source_account_id == account_id,  # type: ignore[operator]
                    Transfer.dest_account_id == account_id,  # type: ignore[operator]
                )
            )
            .all()
        )

    def count_transfers_for_account(self, account_id: str) -> int:
        return (
            self.session.query(Transfer)
            .filter(
                or_(
                    Transfer.source_account_id == account_id,  # type: ignore[operator]
                    Transfer.dest_account_id == account_id,  # type: ignore[operator]
                )
            )
            .count()
        )

    def list_transfers(self, skip: int = 0, limit: int = 50) -> list[Transfer]:
        return (
            self.session.query(Transfer)
            .order_by(transfers.c.transfer_date, transfers.c.transfer_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_posting(self, posting_id: str) -> Posting | None:
        return self.session.query(Posting).filter_by(posting_id=posting_id).one_or_none()

    def list_postings(
        self, account_id: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[Posting]:
        query = self.session.query(Posting)
        if account_id is not None:
            query = query.filter_by(account_id=account_id)
        return (
            query.order_by(postings.c.posting_date, postings.c.posting_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_postings_for_account(self, account_id: str) -> int:
        from app.domain.model import Posting

        return self.session.query(Posting).filter_by(account_id=account_id).count()

    # Category methods
    def add_category(self, category: Category):
        self.session.add(category)

    def get_category(self, category_id: str) -> Category | None:
        return self.session.query(Category).filter_by(category_id=category_id).one_or_none()

    def get_category_by_name(self, name: str) -> Category | None:
        return self.session.query(Category).filter_by(name=name).first()

    def list_categories(self, skip: int = 0, limit: int = 50) -> list[Category]:
        return (
            self.session.query(Category)
            .order_by(categories.c.name, categories.c.category_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete_category(self, category: Category) -> None:
        self.session.delete(category)

    def count_postings_for_category(self, category_id: str) -> int:
        from app.domain.model import Posting

        return self.session.query(Posting).filter_by(category_id=category_id).count()
