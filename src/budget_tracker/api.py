from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.exc import UnmappedClassError

from budget_tracker.db import metadata
from budget_tracker.db import start_mappers
from budget_tracker.model import (
    Account,
    DuplicateAccountNameError,
    InvalidInitialBalanceError,
)
from budget_tracker.repository import AbstractRepository, SqlAlchemyRepository
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
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


def get_repository(
    session: Session = Depends(get_db_session),
) -> AbstractRepository:
    """Dependency that provides a repository instance."""
    return SqlAlchemyRepository(session)


@app.get("/accounts", response_model=list[AccountResponse])
def list_accounts(repo: AbstractRepository = Depends(get_repository)):
    return repo.list_all()


@app.post("/accounts", status_code=201, response_model=AccountResponse)
def create_account_endpoint(
    account: AccountCreate,
    repo: AbstractRepository = Depends(get_repository),
):
    try:
        new_account = create_account(
            repo=repo,
            **account.model_dump(),
        )
    except DuplicateAccountNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidInitialBalanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        repo.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return new_account
