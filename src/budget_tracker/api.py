from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.exc import UnmappedClassError

from budget_tracker.db import metadata
from budget_tracker.db import start_mappers
from budget_tracker.model import Account, DuplicateAccountNameError
from budget_tracker.repository import SqlAlchemyRepository
from budget_tracker.schemas import AccountCreate, AccountResponse
from budget_tracker.services import create_account

try:
    class_mapper(Account)
except UnmappedClassError:
    # Mappers not yet configured, so configure them
    start_mappers()
except ArgumentError:
    # Mappers might be already started by tests or other imports
    pass

app = FastAPI()

# Setup database (using file-based SQLite database 'budget.db';
# this URL could be made configurable via environment variables)
engine = create_engine("sqlite:///budget.db")
# Create tables (normally done via migration, but for quick start:
metadata.create_all(engine)

session_factory = sessionmaker(bind=engine)


def get_db_session():
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@app.get("/accounts", response_model=list[AccountResponse])
def list_accounts(session: Session = Depends(get_db_session)):
    repository = SqlAlchemyRepository(session)
    return repository.list_all()


@app.post("/accounts", status_code=201, response_model=AccountResponse)
def create_account_endpoint(
    account: AccountCreate, session: Session = Depends(get_db_session)
):
    repository = SqlAlchemyRepository(session)

    try:
        new_account = create_account(
            repo=repository,
            session=session,
            **account.model_dump(),
        )
    except DuplicateAccountNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return new_account
