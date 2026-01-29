from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.orm.util import class_mapper

from app.adapters.orm import metadata, start_mappers
from app.domain.model import Account
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.adapters.unit_of_work import SqlAlchemyUnitOfWork

DATABASE_URL = "sqlite:///budget.db"


def _ensure_mappers_started() -> None:
    """Initialize ORM mappers if they are not already configured."""
    try:
        class_mapper(Account)
    except UnmappedClassError:
        start_mappers()
    except ArgumentError:
        # Mappers might be already started by tests or other imports
        pass


_ensure_mappers_started()

# Setup database (using file-based SQLite database 'budget.db';
# this URL could be made configurable via environment variables)
engine = create_engine(DATABASE_URL)
# Create tables (normally done via migration, but for quick start)
metadata.create_all(engine)

session_factory = sessionmaker(bind=engine)


def get_db_session():
    """Yield a database session tied to the configured engine."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_unit_of_work(
    session: Annotated[Session, Depends(get_db_session)],
) -> AbstractUnitOfWork:
    """Dependency that provides a unit of work instance."""
    return SqlAlchemyUnitOfWork(session)
