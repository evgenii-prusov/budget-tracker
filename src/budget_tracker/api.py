from decimal import Decimal
from fastapi import FastAPI, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from budget_tracker.db import metadata, start_mappers
from budget_tracker.model import Account
from budget_tracker.repository import SqlAlchemyRepository


# Common ISO 4217 currency codes
VALID_CURRENCIES = {
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CHF",
    "CAD",
    "AUD",
    "NZD",
    "SEK",
    "NOK",
    "DKK",
    "ISK",
    "CZK",
    "PLN",
    "HUF",
    "RON",
    "BGN",
    "HRK",
    "RUB",
    "TRY",
    "BRL",
    "MXN",
    "ARS",
    "CLP",
    "COP",
    "PEN",
    "CNY",
    "HKD",
    "INR",
    "IDR",
    "KRW",
    "MYR",
    "PHP",
    "SGD",
    "THB",
    "VND",
    "ZAR",
    "ILS",
    "SAR",
    "AED",
    "KWD",
    "QAR",
    "BHD",
    "OMR",
    "JOD",
    "EGP",
    "MAD",
    "TND",
}


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

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        """Validate that currency is a valid ISO 4217 code."""
        if value.upper() not in VALID_CURRENCIES:
            raise ValueError(
                f"Invalid currency code: {value}. "
                "Must be a valid ISO 4217 currency code."
            )
        return value.upper()


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
    session.commit()
    return {"id": new_account.id}
