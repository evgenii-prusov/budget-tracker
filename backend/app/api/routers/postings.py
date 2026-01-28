from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.api.dependencies import get_repository
from app.api.schemas import PostingCreate
from app.api.schemas import PostingResponse
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import InsufficientFundsError
from app.domain.exceptions import PostingNotFoundError
from app.domain.model import PostingType
from app.service_layer.abstract_repository import AbstractRepository
from app.service_layer.services import create_posting
from app.service_layer.services import get_posting


router = APIRouter(
    prefix="/postings",
    tags=["postings"],
)


@router.post("/", response_model=PostingResponse, status_code=status.HTTP_201_CREATED)
def create_posting_endpoint(
    posting: PostingCreate,
    repo: Annotated[AbstractRepository, Depends(get_repository)],
):
    try:
        # Convert schema enum to domain enum
        domain_posting_type = PostingType(posting.posting_type.value)

        new_posting = create_posting(
            repo,
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{posting_id}", response_model=PostingResponse)
def get_posting_endpoint(
    posting_id: str,
    repo: Annotated[AbstractRepository, Depends(get_repository)],
):
    try:
        return get_posting(repo, posting_id=posting_id)
    except PostingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
