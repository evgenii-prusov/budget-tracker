from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.domain.exceptions import AccountNotFoundError
from app.domain.exceptions import AccountHasTransfersError
from app.service_layer.abstract_repository import AbstractRepository
from app.api.dependencies import get_repository
from app.api.schemas import AccountResponse
from app.api.schemas import AccountCreate
from app.service_layer.services import create_account
from app.service_layer.services import delete_account


router = APIRouter()
RepoDep = Annotated[AbstractRepository, Depends(get_repository)]


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(repo: RepoDep):
    return repo.list_all()


@router.post("/accounts", status_code=201, response_model=AccountResponse)
def create_account_endpoint(account: AccountCreate, repo: RepoDep):
    try:
        new_account = create_account(repo=repo, **account.model_dump())
    except DuplicateAccountNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidInitialBalanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        repo.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return new_account


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account_endpoint(account_id: str, repo: RepoDep):
    try:
        delete_account(repo=repo, account_id=account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AccountHasTransfersError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        repo.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return None
