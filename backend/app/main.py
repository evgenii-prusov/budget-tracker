from typing import Annotated
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_db_session
from app.dependencies import get_repository
from app.model import DuplicateAccountNameError
from app.model import InvalidInitialBalanceError
from app.repository import AbstractRepository
from app.schemas import AccountCreate
from app.schemas import AccountResponse
from app.services import create_account

__all__ = ["app", "get_db_session", "get_repository"]

app = FastAPI()
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RepoDep = Annotated[AbstractRepository, Depends(get_repository)]


@app.get("/accounts", response_model=list[AccountResponse])
def list_accounts(repo: RepoDep):
    return repo.list_all()


@app.post("/accounts", status_code=201, response_model=AccountResponse)
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
