"""Unit tests for PostgresOAuthProvider.

Uses testcontainers (PostgreSQL) following the project's integration test pattern.
Tests cover the full OAuth provider protocol: client registration, authorization,
code exchange, token refresh, token loading, and revocation.
"""

import time

import pytest
import sqlalchemy as sa
from mcp.server.auth.provider import AuthorizationParams
from mcp.shared.auth import OAuthClientInformationFull

from app.mcp.oauth_provider import (
    ACCESS_TOKEN_EXPIRY_SECONDS,
    PostgresOAuthProvider,
    oauth_tables_metadata,
)

TEST_BASE_URL = "http://localhost:8000/mcp"
TEST_PASSWORD_HASH = (
    "$2b$12$6FQtafu8y3qr8QlpySKC0eBSjp97K0aLabTrguTBJoocKizymv1xy"  # hash of "test-password"
)


@pytest.fixture(scope="module")
def oauth_engine():
    """Spin up a throwaway Postgres container for OAuth tests."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:17") as pg:
        engine = sa.create_engine(pg.get_connection_url())
        oauth_tables_metadata.create_all(engine)
        yield engine


@pytest.fixture
def provider(oauth_engine):
    """Fresh PostgresOAuthProvider connected to test DB, with cleanup between tests."""
    p = PostgresOAuthProvider(
        engine=oauth_engine,
        owner_password_hash=TEST_PASSWORD_HASH,
        base_url=TEST_BASE_URL,
    )
    yield p
    # Clean up all tables after each test
    with oauth_engine.connect() as conn:
        for table in reversed(oauth_tables_metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


def _make_client_info(client_id: str = "test-client") -> OAuthClientInformationFull:
    return OAuthClientInformationFull(
        client_id=client_id,
        client_secret="test-secret",
        redirect_uris=["http://localhost:3000/callback"],
    )


def _make_auth_params(**overrides) -> AuthorizationParams:
    defaults = dict(
        state="test-state",
        scopes=["read", "write"],
        code_challenge="test-challenge-abc123",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
    )
    defaults.update(overrides)
    return AuthorizationParams(**defaults)


# ── Client registration ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_and_get_client(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    loaded = await provider.get_client("test-client")
    assert loaded is not None
    assert loaded.client_id == "test-client"
    assert loaded.client_secret == "test-secret"
    assert str(loaded.redirect_uris[0]) == "http://localhost:3000/callback"


@pytest.mark.asyncio
async def test_get_client_not_found(provider):
    result = await provider.get_client("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_register_client_updates_existing(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    updated = _make_client_info()
    updated.client_secret = "new-secret"
    await provider.register_client(updated)

    loaded = await provider.get_client("test-client")
    assert loaded.client_secret == "new-secret"


# ── Authorization ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_authorize_returns_login_redirect(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    params = _make_auth_params()
    redirect_url = await provider.authorize(client_info, params)

    assert "/login?" in redirect_url
    assert "client_id=test-client" in redirect_url
    assert "redirect_uri=" in redirect_url
    assert "state=test-state" in redirect_url
    assert "code_challenge=test-challenge-abc123" in redirect_url


# ── Authorization code exchange ──────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_load_authorization_code(provider):
    """Test the create_authorization_code + load_authorization_code round-trip."""
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=["read", "write"],
        code_challenge="test-challenge",
    )
    assert code is not None

    loaded = await provider.load_authorization_code(client_info, code)
    assert loaded is not None
    assert loaded.code == code
    assert loaded.client_id == "test-client"
    assert loaded.scopes == ["read", "write"]
    assert loaded.code_challenge == "test-challenge"


@pytest.mark.asyncio
async def test_load_authorization_code_wrong_client(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=[],
        code_challenge="challenge",
    )

    other_client = _make_client_info("other-client")
    result = await provider.load_authorization_code(other_client, code)
    assert result is None


@pytest.mark.asyncio
async def test_load_authorization_code_expired(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=[],
        code_challenge="challenge",
        expires_at=time.time() - 10,  # already expired
    )

    result = await provider.load_authorization_code(client_info, code)
    assert result is None


@pytest.mark.asyncio
async def test_exchange_authorization_code(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=["read"],
        code_challenge="challenge",
    )

    auth_code = await provider.load_authorization_code(client_info, code)
    token = await provider.exchange_authorization_code(client_info, auth_code)

    assert token.access_token is not None
    assert token.refresh_token is not None
    assert token.token_type == "Bearer"
    assert token.expires_in == ACCESS_TOKEN_EXPIRY_SECONDS

    # Code should be consumed — loading again returns None
    result = await provider.load_authorization_code(client_info, code)
    assert result is None


# ── Access token loading ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_access_token(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=["read"],
        code_challenge="challenge",
    )
    auth_code = await provider.load_authorization_code(client_info, code)
    oauth_token = await provider.exchange_authorization_code(client_info, auth_code)

    access = await provider.load_access_token(oauth_token.access_token)
    assert access is not None
    assert access.client_id == "test-client"
    assert access.scopes == ["read"]


@pytest.mark.asyncio
async def test_load_access_token_not_found(provider):
    result = await provider.load_access_token("nonexistent-token")
    assert result is None


# ── Refresh token flow ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_token_flow(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=["read", "write"],
        code_challenge="challenge",
    )
    auth_code = await provider.load_authorization_code(client_info, code)
    oauth_token = await provider.exchange_authorization_code(client_info, auth_code)

    # Load refresh token
    refresh = await provider.load_refresh_token(client_info, oauth_token.refresh_token)
    assert refresh is not None
    assert refresh.client_id == "test-client"

    # Exchange refresh token for new tokens (token rotation)
    new_oauth_token = await provider.exchange_refresh_token(client_info, refresh, ["read", "write"])
    assert new_oauth_token.access_token != oauth_token.access_token
    assert new_oauth_token.refresh_token != oauth_token.refresh_token

    # Old access token should be revoked
    old_access = await provider.load_access_token(oauth_token.access_token)
    assert old_access is None

    # New access token should work
    new_access = await provider.load_access_token(new_oauth_token.access_token)
    assert new_access is not None


@pytest.mark.asyncio
async def test_load_refresh_token_wrong_client(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=[],
        code_challenge="challenge",
    )
    auth_code = await provider.load_authorization_code(client_info, code)
    oauth_token = await provider.exchange_authorization_code(client_info, auth_code)

    other_client = _make_client_info("other-client")
    result = await provider.load_refresh_token(other_client, oauth_token.refresh_token)
    assert result is None


# ── Token revocation ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_revoke_access_token(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=["read"],
        code_challenge="challenge",
    )
    auth_code = await provider.load_authorization_code(client_info, code)
    oauth_token = await provider.exchange_authorization_code(client_info, auth_code)

    # Load and revoke the access token
    access = await provider.load_access_token(oauth_token.access_token)
    await provider.revoke_token(access)

    # Both access and refresh tokens should be gone
    assert await provider.load_access_token(oauth_token.access_token) is None
    assert await provider.load_refresh_token(client_info, oauth_token.refresh_token) is None


@pytest.mark.asyncio
async def test_revoke_refresh_token(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=["read"],
        code_challenge="challenge",
    )
    auth_code = await provider.load_authorization_code(client_info, code)
    oauth_token = await provider.exchange_authorization_code(client_info, auth_code)

    # Load and revoke the refresh token
    refresh = await provider.load_refresh_token(client_info, oauth_token.refresh_token)
    await provider.revoke_token(refresh)

    # Both should be gone
    assert await provider.load_access_token(oauth_token.access_token) is None
    assert await provider.load_refresh_token(client_info, oauth_token.refresh_token) is None


# ── verify_token (TokenVerifier protocol) ────────────────────────────


@pytest.mark.asyncio
async def test_verify_token_delegates_to_load_access_token(provider):
    client_info = _make_client_info()
    await provider.register_client(client_info)

    code = await provider.create_authorization_code(
        client_id="test-client",
        redirect_uri="http://localhost:3000/callback",
        redirect_uri_provided_explicitly=True,
        scopes=["read"],
        code_challenge="challenge",
    )
    auth_code = await provider.load_authorization_code(client_info, code)
    oauth_token = await provider.exchange_authorization_code(client_info, auth_code)

    result = await provider.verify_token(oauth_token.access_token)
    assert result is not None
    assert result.client_id == "test-client"


@pytest.mark.asyncio
async def test_verify_token_returns_none_for_invalid(provider):
    result = await provider.verify_token("invalid-token")
    assert result is None
