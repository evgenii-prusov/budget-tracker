from decimal import Decimal
from fastapi import FastAPI
from fastapi import Depends
from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from budget_tracker.db import metadata
from budget_tracker.db import start_mappers
from budget_tracker.model import Account
from budget_tracker.repository import SqlAlchemyRepository


try:
    start_mappers()
except Exception:
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


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    currency: str
    initial_balance: Decimal = Decimal("0.0")


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
    session.commit()
    return AccountResponse(
        id=new_account.id,
        name=new_account.name,
        currency=new_account.currency,
        initial_balance=new_account.initial_balance,
    )
