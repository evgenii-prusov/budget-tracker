from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.api.dependencies import get_unit_of_work
from app.api.schemas import AccountResponse
from app.api.schemas import AccountCreate
from app.api.schemas import AccountUpdate
from app.service_layer.services import create_account
from app.service_layer.services import delete_account
from app.service_layer.services import get_account
from app.service_layer.services import update_account_name


router = APIRouter()
UoWDep = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(uow: UoWDep):
    return uow.repo.list_all()


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account_endpoint(account_id: str, uow: UoWDep):
    try:
        account = get_account(uow=uow, account_id=account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return account


@router.post("/accounts", status_code=201, response_model=AccountResponse)
def create_account_endpoint(account: AccountCreate, uow: UoWDep):
    try:
        new_account = create_account(uow=uow, **account.model_dump())
    except DuplicateAccountNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidInitialBalanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return new_account


@router.patch("/accounts/{account_id}", response_model=AccountResponse)
def update_account_name_endpoint(
    account_id: str, account_update: AccountUpdate, uow: UoWDep
):
    try:
        updated_account = update_account_name(
            uow=uow, account_id=account_id, new_name=account_update.name
        )
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DuplicateAccountNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return updated_account


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account_endpoint(account_id: str, uow: UoWDep):
    try:
        delete_account(uow=uow, account_id=account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AccountHasTransfersError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return None
