from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import InvalidCurrencyError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError
from app.domain.exceptions import AccountHasPostingsError
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.api.dependencies import get_unit_of_work
from app.api.schemas import AccountResponse
from app.api.schemas import AccountCreate
from app.api.schemas import AccountUpdate
from app.service_layer.services import create_account
from app.service_layer.services import delete_account
from app.service_layer.services import get_account
from app.service_layer.services import list_accounts as list_accounts_service
from app.service_layer.services import update_account_name
from app.service_layer.services import update_account_description


router = APIRouter()
UoWDep = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(
    uow: UoWDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return list_accounts_service(uow=uow, skip=skip, limit=limit)


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
    except (InvalidInitialBalanceError, InvalidCurrencyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return new_account


@router.patch("/accounts/{account_id}", response_model=AccountResponse)
def update_account_endpoint(account_id: str, account_update: AccountUpdate, uow: UoWDep):
    fields = account_update.model_fields_set
    try:
        account = None
        if "name" in fields and account_update.name is not None:
            account = update_account_name(
                uow=uow, account_id=account_id, new_name=account_update.name
            )
        if "description" in fields:
            account = update_account_description(
                uow=uow, account_id=account_id, description=account_update.description
            )
        if account is None:
            account = get_account(uow=uow, account_id=account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DuplicateAccountNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return account


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account_endpoint(account_id: str, uow: UoWDep):
    try:
        delete_account(uow=uow, account_id=account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (AccountHasTransfersError, AccountHasPostingsError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return None
