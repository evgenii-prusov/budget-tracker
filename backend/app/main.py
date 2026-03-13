from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from app.api.auth import verify_api_key
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import accounts
from app.api.routers import categories
from app.api.routers import postings
from app.api.routers import transfers
from app.api.routers import reports
from app.core.logging_config import setup_logging
from app.api.middleware import LoggingMiddleware
from app.core.db import Database
from app.mcp.server import create_mcp_app

# Create MCP app at module level so its lifespan can be composed below
mcp_app = create_mcp_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    app.state.db = Database()
    app.state.db.init()
    async with mcp_app.lifespan(mcp_app):
        yield
    app.state.db.dispose()


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.include_router(accounts.router, dependencies=[Depends(verify_api_key)])
app.include_router(categories.router, dependencies=[Depends(verify_api_key)])
app.include_router(postings.router, dependencies=[Depends(verify_api_key)])
app.include_router(transfers.router, dependencies=[Depends(verify_api_key)])
app.include_router(reports.router, dependencies=[Depends(verify_api_key)])

# Mount MCP server (has its own auth via Bearer token verification)
app.mount("/mcp", mcp_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
