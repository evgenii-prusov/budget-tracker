from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import verify_api_key
from app.api.middleware import LoggingMiddleware
from app.api.routers import accounts, categories, dashboard, postings, reports, settings, transfers
from app.core.config import get_cors_origins
from app.core.db import Database
from app.core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    app.state.db = Database()
    app.state.db.init()
    yield
    app.state.db.dispose()


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.include_router(accounts.router, dependencies=[Depends(verify_api_key)])
app.include_router(categories.router, dependencies=[Depends(verify_api_key)])
app.include_router(postings.router, dependencies=[Depends(verify_api_key)])
app.include_router(transfers.router, dependencies=[Depends(verify_api_key)])
app.include_router(reports.router, dependencies=[Depends(verify_api_key)])
app.include_router(dashboard.router, dependencies=[Depends(verify_api_key)])
app.include_router(settings.router, dependencies=[Depends(verify_api_key)])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
