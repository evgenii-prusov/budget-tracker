from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.model import Transfer
from app.adapters.orm import transfers
from app.service_layer.abstract_transfer_repository import AbstractTransferRepository


class SqlAlchemyTransferRepository(AbstractTransferRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, transfer: Transfer) -> None:
        self.session.add(transfer)

    def get(self, transfer_id: str) -> Transfer | None:
        return (
            self.session.execute(select(Transfer).filter_by(transfer_id=transfer_id))
            .scalars()
            .one_or_none()
        )

    def delete(self, transfer: Transfer) -> None:
        self.session.delete(transfer)

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Transfer]:
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
