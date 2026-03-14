from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session, selectinload

from app.domain.model import Account
from app.adapters.orm import accounts, postings
from app.service_layer.abstract_account_repository import AbstractAccountRepository


def _select_account_with_balance_relations():
    """Return a base SELECT for Account with all balance-relevant relationships eagerly loaded.

    Eagerly loading _postings, _outgoing_transfers, and _incoming_transfers prevents
    N+1 lazy-load queries when Account.balance is accessed during serialization.
    Used by read paths that return Account objects to the API (get, list_all).
    """
    return select(Account).options(
        selectinload(Account._postings),  # type: ignore[attr-defined]  # set by imperative mapping
        selectinload(Account._outgoing_transfers),  # type: ignore[attr-defined]
        selectinload(Account._incoming_transfers),  # type: ignore[attr-defined]
    )


def _select_account_with_postings_only():
    """Return a base SELECT for Account with only _postings eagerly loaded.

    Used by read paths that need access to postings but not transfers
    (e.g. get_by_posting_id, which is only used to look up and return a single Posting).
    """
    return select(Account).options(
        selectinload(Account._postings),  # type: ignore[attr-defined]  # set by imperative mapping
    )


class SqlAlchemyAccountRepository(AbstractAccountRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account) -> None:
        self.session.add(account)

    def get(self, account_id: str) -> Account | None:
        return (
            self.session.execute(
                _select_account_with_balance_relations().filter_by(account_id=account_id)
            )
            .scalars()
            .one_or_none()
        )

    def get_by_name(self, name: str) -> Account | None:
        # Used only for duplicate-name checks; no relationship access required.
        return self.session.execute(select(Account).filter_by(name=name)).scalars().first()

    def get_by_posting_id(self, posting_id: str) -> Account | None:
        stmt = (
            _select_account_with_postings_only()
            .join(postings, accounts.c.account_id == postings.c.account_id)
            .where(postings.c.posting_id == posting_id)
        )
        return self.session.execute(stmt).scalars().one_or_none()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Account]:
        return list(
            self.session.execute(
                _select_account_with_balance_relations()
                .order_by(accounts.c.name, accounts.c.account_id)
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def delete(self, account: Account) -> None:
        self.session.delete(account)

    def delete_posting_by_id(self, posting_id: str) -> bool:
        result: CursorResult = self.session.execute(  # type: ignore[assignment]
            delete(postings).where(postings.c.posting_id == posting_id)
        )
        return result.rowcount > 0
