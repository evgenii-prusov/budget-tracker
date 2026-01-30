from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi import Query

from app.api.dependencies import get_unit_of_work
from app.api.schemas import PostingCreate
from app.api.schemas import PostingResponse
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import InsufficientFundsError
from app.domain.exceptions import PostingNotFoundError
from app.domain.model import PostingType
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.service_layer.services import create_posting
from app.service_layer.services import delete_posting
from app.service_layer.services import get_posting
from app.service_layer.services import list_postings


router = APIRouter(
    prefix="/postings",
    tags=["postings"],
)

UoWDep = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]


@router.get("/", response_model=list[PostingResponse])
def list_postings_endpoint(
    uow: UoWDep,
    account_id: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return list_postings(uow, account_id=account_id, skip=skip, limit=limit)


@router.post("/", response_model=PostingResponse, status_code=status.HTTP_201_CREATED)
def create_posting_endpoint(
    posting: PostingCreate,
    uow: UoWDep,
):
    try:
        # Convert schema enum to domain enum
        domain_posting_type = PostingType(posting.posting_type.value)

        new_posting = create_posting(
            uow,
            account_id=posting.account_id,
            amount=posting.amount,
            posting_date=posting.posting_date,
            posting_type=domain_posting_type,
            category_id=posting.category_id,
        )
        return new_posting
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CategoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@router.get("/{posting_id}", response_model=PostingResponse)
def get_posting_endpoint(
    posting_id: str,
    uow: UoWDep,
):
    try:
        return get_posting(uow, posting_id=posting_id)
    except PostingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{posting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_posting_endpoint(
    posting_id: str,
    uow: UoWDep,
):
    try:
        delete_posting(uow, posting_id=posting_id)
    except PostingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
