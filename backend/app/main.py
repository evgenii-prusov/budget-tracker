from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from app.api.auth import verify_api_key
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import accounts
from app.api.routers import categories
from app.api.routers import postings
from app.api.routers import transfers
from app.core.logging_config import setup_logging
from app.api.middleware import LoggingMiddleware
from app.core.db import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    setup_logging()
    app.state.db = Database()
    app.state.db.init()
    yield
    # Shutdown: Dispose database connection
    app.state.db.dispose()


app = FastAPI(lifespan=lifespan, dependencies=[Depends(verify_api_key)])
app.add_middleware(LoggingMiddleware)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(postings.router)
app.include_router(transfers.router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
