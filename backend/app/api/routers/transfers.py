from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi import Query

from app.api.dependencies import get_unit_of_work
from app.api.schemas import TransferCreate
from app.api.schemas import TransferResponse
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import InsufficientFundsError
from app.domain.exceptions import TransferNotFoundError
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.service_layer.services import create_transfer
from app.service_layer.services import delete_transfer
from app.service_layer.services import get_transfer
from app.service_layer.services import list_transfers


router = APIRouter(
    prefix="/transfers",
    tags=["transfers"],
)

UoWDep = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer_endpoint(
    transfer: TransferCreate,
    uow: UoWDep,
):
    try:
        new_transfer = create_transfer(
            uow,
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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@router.get("/", response_model=list[TransferResponse])
def list_transfers_endpoint(
    uow: UoWDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return list_transfers(uow, skip=skip, limit=limit)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer_endpoint(
    transfer_id: str,
    uow: UoWDep,
):
    try:
        return get_transfer(uow, transfer_id=transfer_id)
    except TransferNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transfer_endpoint(
    transfer_id: str,
    uow: UoWDep,
):
    try:
        delete_transfer(uow, transfer_id=transfer_id)
    except TransferNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
