from typing import Annotated
from fastapi import Depends
from fastapi import Request
from sqlalchemy.orm import Session

from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.adapters.unit_of_work import SqlAlchemyUnitOfWork


def get_db_session(request: Request):
    """Yield a database session tied to the configured engine."""
    session = request.app.state.db.get_session()
    try:
        yield session
    finally:
        session.close()


def get_unit_of_work(
    session: Annotated[Session, Depends(get_db_session)],
) -> AbstractUnitOfWork:
    """Dependency that provides a unit of work instance."""
    return SqlAlchemyUnitOfWork(session)
