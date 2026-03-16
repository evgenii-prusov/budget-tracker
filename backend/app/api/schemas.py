from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.domain.model import CategoryType, PostingType


class AccountCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[\w]+(?:[ _-][\w]+)*$",
        description="Account name (3-100 characters, Unicode letters/digits allowed)",
    )
    currency: str
    initial_balance: Decimal = Decimal(0)
    is_savings: bool = False
    description: str | None = Field(None, max_length=500)


class AccountUpdate(BaseModel):
    name: str | None = Field(
        None,
        min_length=3,
        max_length=100,
        pattern=r"^[\w]+(?:[ _-][\w]+)*$",
        description="New account name (3-100 characters, Unicode letters/digits allowed)",
    )
    description: str | None = Field(None, max_length=500)
    initial_balance: Decimal | None = Field(None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_field(cls, data: dict) -> dict:
        if not data:
            raise ValueError("At least one field must be provided for update")
        if "name" in data and data["name"] is None:
            raise ValueError("Account name cannot be null")
        if "initial_balance" in data and data["initial_balance"] is None:
            raise ValueError("Initial balance cannot be null")
        return data


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    name: str
    currency: str
    initial_balance: Decimal = Decimal(0)
    is_savings: bool
    balance: Decimal = Decimal(0)
    description: str | None = None


class CategoryCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Category name",
    )
    category_type: CategoryType
    parent_id: str | None = None
    description: str | None = Field(None, max_length=500)


class CategoryUpdate(BaseModel):
    name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="New category name",
    )
    description: str | None = Field(None, max_length=500)
    parent_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_field(cls, data: dict) -> dict:
        if not data:
            raise ValueError("At least one field must be provided for update")
        if "name" in data and data["name"] is None:
            raise ValueError("Category name cannot be null")
        return data


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: str
    name: str
    category_type: CategoryType
    parent_id: str | None
    description: str | None = None


class CategoryWithChildrenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: str
    name: str
    category_type: CategoryType
    parent_id: str | None
    description: str | None = None
    children: list[CategoryResponse] = []


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


class CategorySpendingResponse(BaseModel):
    parent_category_id: str
    parent_category_name: str
    currency: str
    total: Decimal


class SpendingReportResponse(BaseModel):
    period: str
    start_date: date
    end_date: date
    rows: list[CategorySpendingResponse]
