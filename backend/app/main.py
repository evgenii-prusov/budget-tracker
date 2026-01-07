from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_db_session, get_repository
from app.model import DuplicateAccountNameError, InvalidInitialBalanceError
from app.repository import AbstractRepository
from app.schemas import AccountCreate, AccountResponse
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


@app.get("/accounts", response_model=list[AccountResponse])
def list_accounts(repo: AbstractRepository = Depends(get_repository)):
    return repo.list_all()


@app.post("/accounts", status_code=201, response_model=AccountResponse)
def create_account_endpoint(
    account: AccountCreate,
    repo: AbstractRepository = Depends(get_repository),
):
    try:
        new_account = create_account(
            repo=repo,
            **account.model_dump(),
        )
    except DuplicateAccountNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidInitialBalanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        repo.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return new_account
