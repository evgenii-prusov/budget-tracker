from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.domain.exceptions import DuplicateAccountNameError
from app.domain.exceptions import InvalidInitialBalanceError
from app.repository import AbstractRepository
from app.dependencies import get_repository
from app.schemas import AccountResponse
from app.schemas import AccountCreate
from app.services import create_account


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
