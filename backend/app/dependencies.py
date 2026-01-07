from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.orm.util import class_mapper

from app.db import metadata, start_mappers
from app.model import Account
from app.repository import AbstractRepository, SqlAlchemyRepository

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


def get_repository(
    session: Session = Depends(get_db_session),
) -> AbstractRepository:
    """Dependency that provides a repository instance."""
    return SqlAlchemyRepository(session)
