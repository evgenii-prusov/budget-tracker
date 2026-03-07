from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.model import Account
from app.adapters.orm import accounts, postings
from app.service_layer.abstract_account_repository import AbstractAccountRepository


class SqlAlchemyAccountRepository(AbstractAccountRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account) -> None:
        self.session.add(account)

    def get(self, account_id: str) -> Account | None:
        return (
            self.session.execute(select(Account).filter_by(account_id=account_id))
            .scalars()
            .one_or_none()
        )

    def get_by_name(self, name: str) -> Account | None:
        return self.session.execute(select(Account).filter_by(name=name)).scalars().first()

    def get_by_posting_id(self, posting_id: str) -> Account | None:
        stmt = (
            select(Account)
            .join(postings, accounts.c.account_id == postings.c.account_id)
            .where(postings.c.posting_id == posting_id)
        )
        return self.session.execute(stmt).scalars().one_or_none()

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
