from decimal import Decimal
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict


class PostingType(StrEnum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"


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

    account_id: str
    name: str
    currency: str
    initial_balance: Decimal = Decimal(0)


class CategoryCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Category name",
    )


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: str
    name: str


class PostingCreate(BaseModel):
    account_id: str
    amount: Decimal = Field(..., gt=0)
    posting_date: date
    posting_type: PostingType
    category_id: str | None = None


class PostingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    posting_id: str
    account_id: str
    amount: Decimal
    posting_date: date
    posting_type: PostingType
    category_id: str | None
