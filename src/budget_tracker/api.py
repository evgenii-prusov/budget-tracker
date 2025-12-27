from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.exc import UnmappedClassError

from budget_tracker.db import metadata
from budget_tracker.db import start_mappers
from budget_tracker.model import Account
from budget_tracker.repository import SqlAlchemyRepository


# Common ISO 4217 currency codes
VALID_CURRENCIES = {
    "USD",
    "EUR",
    "JPY",
    "RUB",
    "AED",
}


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


def validate_currency(value: str) -> str:
    """Validate that currency is a valid ISO 4217 code."""
    if value.upper() not in VALID_CURRENCIES:
        raise ValueError(
            f"Invalid currency code: {value}. "
            "Must be a valid ISO 4217 currency code."
        )
    return value.upper()


class AccountCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern="^[a-zA-Z0-9][a-zA-Z0-9 _-]*$",
        description=(
            "Account name (3-100 characters, must start with alphanumeric, "
            "can contain spaces, hyphens, underscores)"
        ),
    )
    currency: str
    initial_balance: Decimal = Decimal("0.0")

    @field_validator("currency")
    @classmethod
    def call_validate_currency(cls, value: str) -> str:
        return validate_currency(value)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    currency: str
    initial_balance: Decimal = Decimal("0.0")

    @field_validator("currency")
    @classmethod
    def call_validate_currency(cls, value: str) -> str:
        return validate_currency(value)


@app.get("/accounts", response_model=list[AccountResponse])
def list_accounts(session: Session = Depends(get_db_session)):
    repository = SqlAlchemyRepository(session)
    return repository.list_all()


@app.post("/accounts", status_code=201, response_model=AccountResponse)
def create_account(
    account: AccountCreate, session: Session = Depends(get_db_session)
):
    repository = SqlAlchemyRepository(session)

    new_account = Account(
        id=None,
        name=account.name,
        currency=account.currency,
        initial_balance=account.initial_balance,
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
    return new_account
