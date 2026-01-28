from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.api.dependencies import get_repository
from app.api.schemas import TransferCreate
from app.api.schemas import TransferResponse
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import InsufficientFundsError
from app.domain.exceptions import TransferNotFoundError
from app.service_layer.abstract_repository import AbstractRepository
from app.service_layer.services import create_transfer
from app.service_layer.services import get_transfer
from app.service_layer.services import list_transfers


router = APIRouter(
    prefix="/transfers",
    tags=["transfers"],
)


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer_endpoint(
    transfer: TransferCreate,
    repo: Annotated[AbstractRepository, Depends(get_repository)],
):
    try:
        new_transfer = create_transfer(
            repo,
            source_account_id=transfer.source_account_id,
            dest_account_id=transfer.dest_account_id,
            debit_amount=transfer.debit_amount,
            credit_amount=transfer.credit_amount,
            transfer_date=transfer.transfer_date,
            description=transfer.description,
        )
        return new_transfer
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@router.get("/", response_model=list[TransferResponse])
def list_transfers_endpoint(
    repo: Annotated[AbstractRepository, Depends(get_repository)],
):
    return list_transfers(repo)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer_endpoint(
    transfer_id: str,
    repo: Annotated[AbstractRepository, Depends(get_repository)],
):
    try:
        return get_transfer(repo, transfer_id=transfer_id)
    except TransferNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
