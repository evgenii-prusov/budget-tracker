from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class AccountCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[A-Za-z0-9]+(?:[ _-][A-Za-z0-9]+)*$",
        description="Account name (3-100 characters, must start with alphanumeric)",
    )
    currency: str
    initial_balance: Decimal = Decimal(0)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    currency: str
    initial_balance: Decimal = Decimal("0.0")
