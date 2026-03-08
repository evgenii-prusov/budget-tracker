from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field, ConfigDict

from app.domain.model import PostingType


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


class AccountUpdate(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[A-Za-z0-9]+(?:[ _-][A-Za-z0-9]+)*$",
        description="New account name (3-100 characters, must start with alphanumeric)",
    )


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


class CategoryUpdate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="New category name",
    )


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: str
    name: str


class PostingCreate(BaseModel):
    account_id: str
    amount: Decimal = Field(..., gt=0, le=1_000_000_000)
    posting_date: date
    posting_type: PostingType
    category_id: str | None = None
    payee: str | None = None
    description: str | None = None


class PostingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    posting_id: str
    account_id: str
    amount: Decimal
    posting_date: date
    posting_type: PostingType
    category_id: str | None
    payee: str | None
    description: str | None


class TransferCreate(BaseModel):
    source_account_id: str
    dest_account_id: str
    debit_amount: Decimal = Field(..., gt=0, le=1_000_000_000)
    credit_amount: Decimal = Field(..., gt=0, le=1_000_000_000)
    transfer_date: date
    description: str | None = None


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transfer_id: str
    source_account_id: str
    dest_account_id: str
    debit_amount: Decimal
    credit_amount: Decimal
    transfer_date: date
    description: str | None
