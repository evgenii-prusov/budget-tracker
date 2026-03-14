"""Unit tests for the OAuth login/consent page handler.

Tests cover:
- GET /login renders an HTML form with hidden fields
- POST /login with correct password redirects with authorization code
- POST /login with wrong password re-renders form with error
"""

import pytest
import sqlalchemy as sa
from starlette.testclient import TestClient

from app.mcp.login_handler import create_login_app
from app.mcp.oauth_provider import PostgresOAuthProvider, oauth_tables_metadata

# bcrypt hash of "test-password"
TEST_PASSWORD_HASH = "$2b$12$6FQtafu8y3qr8QlpySKC0eBSjp97K0aLabTrguTBJoocKizymv1xy"
TEST_BASE_URL = "http://localhost:8000/mcp"


@pytest.fixture(scope="module")
def oauth_engine():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:17") as pg:
        engine = sa.create_engine(pg.get_connection_url())
        oauth_tables_metadata.create_all(engine)
        yield engine


@pytest.fixture
def provider(oauth_engine):
    p = PostgresOAuthProvider(
        engine=oauth_engine,
        owner_password_hash=TEST_PASSWORD_HASH,
        base_url=TEST_BASE_URL,
    )
    yield p
    with oauth_engine.connect() as conn:
        for table in reversed(oauth_tables_metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture
def login_client(provider):
    app = create_login_app(provider)
    return TestClient(app, raise_server_exceptions=False)


def _login_params():
    return {
        "client_id": "test-client",
        "redirect_uri": "http://localhost:3000/callback",
        "redirect_uri_provided_explicitly": "True",
        "state": "test-state",
        "code_challenge": "test-challenge",
        "scopes": "read write",
    }


# ── GET /login ───────────────────────────────────────────────────────


def test_get_login_renders_form(login_client):
    resp = login_client.get("/login", params=_login_params())
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "<form" in body
    assert 'name="password"' in body
    assert 'name="client_id"' in body
    assert 'value="test-client"' in body
    assert 'value="test-state"' in body


# ── POST /login with correct password ────────────────────────────────


@pytest.mark.asyncio
async def test_post_login_correct_password_redirects(login_client, provider):
    from mcp.shared.auth import OAuthClientInformationFull

    # Register the client first (so code creation can find it)
    await provider.register_client(
        OAuthClientInformationFull(
            client_id="test-client",
            client_secret="secret",
            redirect_uris=["http://localhost:3000/callback"],
        )
    )

    resp = login_client.post(
        "/login",
        data={
            **_login_params(),
            "password": "test-password",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert location.startswith("http://localhost:3000/callback")
    assert "code=" in location
    assert "state=test-state" in location


# ── POST /login with wrong password ──────────────────────────────────


def test_post_login_wrong_password_shows_error(login_client):
    resp = login_client.post(
        "/login",
        data={
            **_login_params(),
            "password": "wrong-password",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 200
    body = resp.text
    assert "Invalid password" in body
    assert "<form" in body  # form is re-rendered


def test_post_login_empty_password_shows_error(login_client):
    resp = login_client.post(
        "/login",
        data={
            **_login_params(),
            "password": "",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 200
    assert "Invalid password" in resp.text
