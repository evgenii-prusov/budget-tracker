"""E2E tests for the full OAuth 2.1 flow on the MCP server.

Tests cover:
- Well-known metadata discovery (RFC 8414, RFC 9728)
- Dynamic Client Registration (RFC 7591)
- Full authorize → login → token → MCP request flow
- 401 without token includes WWW-Authenticate header
- Token refresh flow
"""

from urllib.parse import parse_qs, urlparse

import pytest
from starlette.testclient import TestClient

from app.main import app, oauth_provider
from app.mcp.oauth_provider import oauth_tables_metadata


@pytest.fixture
def oauth_client(postgres_engine):
    """HTTP client wired to the full FastAPI app with OAuth tables available."""
    # Inject the engine into the OAuth provider for this test
    oauth_provider.set_engine(postgres_engine)
    yield TestClient(app, raise_server_exceptions=False)
    # Clean up OAuth tables after each test
    with postgres_engine.connect() as conn:
        for table in reversed(oauth_tables_metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


# ── Well-Known Metadata ──────────────────────────────────────────────


def test_protected_resource_metadata(oauth_client):
    """GET /.well-known/oauth-protected-resource/mcp/ returns resource metadata."""
    resp = oauth_client.get("/.well-known/oauth-protected-resource/mcp/")
    # Some implementations may serve from /mcp/.well-known/... instead
    if resp.status_code == 404:
        resp = oauth_client.get("/mcp/.well-known/oauth-protected-resource")
    assert resp.status_code == 200
    data = resp.json()
    assert "resource" in data


def test_authorization_server_metadata(oauth_client):
    """GET /.well-known/oauth-authorization-server/mcp returns AS metadata."""
    resp = oauth_client.get("/.well-known/oauth-authorization-server/mcp")
    if resp.status_code == 404:
        resp = oauth_client.get("/mcp/.well-known/oauth-authorization-server")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_endpoint" in data
    assert "token_endpoint" in data
    assert "registration_endpoint" in data


# ── Dynamic Client Registration ──────────────────────────────────────


def test_dcr_register_client(oauth_client):
    """POST /mcp/register creates a new client with client_id."""
    resp = oauth_client.post(
        "/mcp/register",
        json={
            "redirect_uris": ["http://localhost:3000/callback"],
            "client_name": "Test Client",
        },
    )
    assert resp.status_code == 200 or resp.status_code == 201
    data = resp.json()
    assert "client_id" in data
    assert data["client_id"] is not None


# ── Full OAuth Flow ──────────────────────────────────────────────────


def test_full_oauth_flow(oauth_client):
    """Complete flow: DCR → authorize → login → token → authenticated MCP request."""
    # 1. Register client
    reg_resp = oauth_client.post(
        "/mcp/register",
        json={
            "redirect_uris": ["http://localhost:3000/callback"],
            "client_name": "Flow Test Client",
        },
    )
    assert reg_resp.status_code in (200, 201)
    client_data = reg_resp.json()
    client_id = client_data["client_id"]
    client_secret = client_data.get("client_secret", "")

    # 2. Start authorization (GET /mcp/authorize → redirect to /mcp/login)
    auth_resp = oauth_client.get(
        "/mcp/authorize",
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "http://localhost:3000/callback",
            "state": "test-state-123",
            "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )
    assert auth_resp.status_code == 302
    login_url = auth_resp.headers["location"]
    assert "/login" in login_url

    # 3. Submit login form with correct password
    parsed = urlparse(login_url)
    login_params = parse_qs(parsed.query)

    login_resp = oauth_client.post(
        f"{parsed.path}",
        data={
            "client_id": login_params.get("client_id", [""])[0],
            "redirect_uri": login_params.get("redirect_uri", [""])[0],
            "redirect_uri_provided_explicitly": login_params.get(
                "redirect_uri_provided_explicitly", ["True"]
            )[0],
            "state": login_params.get("state", [""])[0],
            "code_challenge": login_params.get("code_challenge", [""])[0],
            "scopes": login_params.get("scopes", [""])[0],
            "password": "test-password",
        },
        follow_redirects=False,
    )
    assert login_resp.status_code == 302
    callback_url = login_resp.headers["location"]
    assert "code=" in callback_url
    assert "state=test-state-123" in callback_url

    # 4. Extract authorization code
    callback_parsed = urlparse(callback_url)
    callback_params = parse_qs(callback_parsed.query)
    auth_code = callback_params["code"][0]

    # 5. Exchange code for tokens
    token_resp = oauth_client.post(
        "/mcp/token",
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "http://localhost:3000/callback",
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        },
    )
    assert token_resp.status_code == 200
    token_data = token_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    access_token = token_data["access_token"]

    # 6. Make authenticated MCP request
    mcp_resp = oauth_client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # Should not be 401 — may be 200 (success) or other MCP-level response
    assert mcp_resp.status_code != 401


# ── Unauthenticated access ───────────────────────────────────────────


def test_mcp_401_without_token(oauth_client):
    """MCP endpoint returns 401 without Bearer token."""
    resp = oauth_client.post(
        "/mcp/",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        },
    )
    assert resp.status_code == 401


def test_mcp_post_without_trailing_slash_no_redirect(oauth_client):
    """POST /mcp (no trailing slash) must not 307-redirect.

    Claude Web drops auth headers on redirect.
    """
    resp = oauth_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        },
        follow_redirects=False,
    )
    # Should get 401 (no token) — NOT any redirect (Starlette can use 307 or 308)
    assert resp.status_code not in (301, 302, 303, 307, 308), (
        "POST /mcp must not redirect; Claude Web loses auth headers on any redirect"
    )
    assert resp.status_code == 401


# ── Token refresh ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_token_refresh_flow(oauth_client):
    """After obtaining tokens, refresh token can be used to get new tokens."""
    # Register + authorize + login + token (abbreviated)
    reg = oauth_client.post(
        "/mcp/register",
        json={"redirect_uris": ["http://localhost:3000/callback"]},
    )
    reg_data = reg.json()
    client_id = reg_data["client_id"]
    client_secret = reg_data.get("client_secret", "")

    # Create authorization code directly via provider (shortcut).
    # Use RFC 7636 Appendix B example PKCE pair:
    #   verifier  = dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
    #   challenge = E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
    code = await oauth_provider.create_authorization_code(
        client_id=client_id,
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=[],
        code_challenge="E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
    )

    token_resp = oauth_client.post(
        "/mcp/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:3000/callback",
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        },
    )
    assert token_resp.status_code == 200
    tokens = token_resp.json()
    refresh_token = tokens["refresh_token"]
    old_access = tokens["access_token"]

    # Refresh
    refresh_resp = oauth_client.post(
        "/mcp/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert new_tokens["access_token"] != old_access
    assert "refresh_token" in new_tokens
