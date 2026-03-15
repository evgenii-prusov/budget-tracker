from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.routing import Route

from app.api.auth import verify_api_key
from app.api.middleware import LoggingMiddleware
from app.api.routers import accounts, categories, postings, reports, transfers
from app.core.config import get_cors_origins
from app.core.db import Database
from app.core.logging_config import setup_logging
from app.mcp.login_handler import _get_login, _post_login
from app.mcp.server import create_mcp_app

# Create MCP app at module level so its lifespan can be composed below
mcp_app, oauth_provider = create_mcp_app()

# Add login routes directly to the MCP Starlette app
mcp_app.routes.insert(0, Route("/login", _get_login, methods=["GET"]))
mcp_app.routes.insert(1, Route("/login", _post_login, methods=["POST"]))
# Inject the oauth_provider into the MCP app's state so login handlers can access it
mcp_app.state.oauth_provider = oauth_provider


class _McpTrailingSlashMiddleware:
    """Rewrite /mcp → /mcp/ at the ASGI scope level to avoid 307 redirects.

    Claude Web sends POST /mcp (no trailing slash) and drops the Authorization
    header when following a redirect. Pure ASGI avoids BaseHTTPMiddleware
    streaming limitations.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("path") == "/mcp":
            scope["path"] = "/mcp/"
            scope["raw_path"] = b"/mcp/"
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    app.state.db = Database()
    app.state.db.init()
    async with mcp_app.lifespan(mcp_app):
        yield
    app.state.db.dispose()


app = FastAPI(lifespan=lifespan)
app.add_middleware(_McpTrailingSlashMiddleware)
app.add_middleware(LoggingMiddleware)
app.include_router(accounts.router, dependencies=[Depends(verify_api_key)])
app.include_router(categories.router, dependencies=[Depends(verify_api_key)])
app.include_router(postings.router, dependencies=[Depends(verify_api_key)])
app.include_router(transfers.router, dependencies=[Depends(verify_api_key)])
app.include_router(reports.router, dependencies=[Depends(verify_api_key)])

# Mount well-known routes at root level (RFC 8414 / RFC 9728 require root-level discovery).
# mcp_path=None because the base_url already includes /mcp.
well_known_routes = oauth_provider.get_well_known_routes(mcp_path=None)
for route in well_known_routes:
    app.routes.insert(0, route)

# Mount MCP server (OAuth 2.1 protected, includes login routes)
app.mount("/mcp", mcp_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
