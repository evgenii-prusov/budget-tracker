from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.domain.model import Account
from app.domain.model import Transfer
from app.service_layer.abstract_repository import AbstractRepository


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account):
        self.session.add(account)

    def get(self, account_id) -> Account:
        return self.session.query(Account).filter_by(account_id=account_id).one()

    def get_by_name(self, name: str) -> Account | None:
        return self.session.query(Account).filter_by(name=name).first()

    def list_all(self) -> list[Account]:
        return self.session.query(Account).all()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def add_transfer(self, transfer: Transfer):
        self.session.add(transfer)

    def get_transfer(self, transfer_id: str) -> Transfer:
        return self.session.query(Transfer).filter_by(transfer_id=transfer_id).one()

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
