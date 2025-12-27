from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from budget_tracker.db import metadata, start_mappers
from budget_tracker.model import Account
from budget_tracker.repository import SqlAlchemyRepository


try:
    start_mappers()
except Exception:
    # Mappers might be already started by tests or other imports
    pass

app = FastAPI()

# Setup database (using in-memory SQLite for demo, or a file-based one)
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


@app.get("/accounts")
def list_accounts(session: Session = Depends(get_db_session)):
    repository = SqlAlchemyRepository(session)
    return repository.list_all()


class AccountCreate(BaseModel):
    name: str
    currency: str
    initial_balance: float = 0.0


@app.post("/accounts", status_code=201)
def create_account(
    account: AccountCreate, session: Session = Depends(get_db_session)
):
    repository = SqlAlchemyRepository(session)

    new_account = Account(
        id=None,
        name=account.name,
        currency=account.currency,
        initial_balance=Decimal(account.initial_balance),
    )

    repository.add(new_account)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Account with name '{account.name}' already exists",
        )
    return {"id": new_account.id}
