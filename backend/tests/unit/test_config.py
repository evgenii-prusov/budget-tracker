import pytest


def test_get_cors_origins_returns_default(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    from app.core.config import get_cors_origins

    assert get_cors_origins() == ["http://localhost:5173"]


def test_get_cors_origins_single_value(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://myapp.azurecontainerapps.io")
    from app.core.config import get_cors_origins

    assert get_cors_origins() == ["https://myapp.azurecontainerapps.io"]


def test_get_cors_origins_multiple_values(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://myapp.azurecontainerapps.io,http://localhost:5173",
    )
    from app.core.config import get_cors_origins

    assert get_cors_origins() == [
        "https://myapp.azurecontainerapps.io",
        "http://localhost:5173",
    ]


def test_get_cors_origins_trailing_comma_ignored(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://myapp.azurecontainerapps.io,")
    from app.core.config import get_cors_origins

    assert get_cors_origins() == ["https://myapp.azurecontainerapps.io"]


def test_get_cors_origins_empty_string_raises(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "")
    from app.core.config import get_cors_origins

    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        get_cors_origins()


def test_get_cors_origins_whitespace_only_raises(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "   ,  ")
    from app.core.config import get_cors_origins

    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        get_cors_origins()


def test_get_api_key_returns_value(monkeypatch):
    monkeypatch.setenv("API_KEY", "my-secret")
    from app.core.config import get_api_key

    assert get_api_key() == "my-secret"


def test_get_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    from app.core.config import get_api_key

    with pytest.raises(ValueError, match="API_KEY"):
        get_api_key()


# ── MCP_BASE_URL ───────────────────────────────────────────────────


def test_get_mcp_base_url_returns_value(monkeypatch):
    monkeypatch.setenv("MCP_BASE_URL", "https://example.com/mcp")
    from app.core.config import get_mcp_base_url

    assert get_mcp_base_url() == "https://example.com/mcp"


def test_get_mcp_base_url_raises_when_missing(monkeypatch):
    monkeypatch.delenv("MCP_BASE_URL", raising=False)
    from app.core.config import get_mcp_base_url

    with pytest.raises(ValueError, match="MCP_BASE_URL"):
        get_mcp_base_url()


# ── OAUTH_OWNER_PASSWORD_HASH ─────────────────────────────────────


def test_get_oauth_owner_password_hash_returns_value(monkeypatch):
    monkeypatch.setenv("OAUTH_OWNER_PASSWORD_HASH", "$2b$12$somehash")
    from app.core.config import get_oauth_owner_password_hash

    assert get_oauth_owner_password_hash() == "$2b$12$somehash"


def test_get_oauth_owner_password_hash_raises_when_missing(monkeypatch):
    monkeypatch.delenv("OAUTH_OWNER_PASSWORD_HASH", raising=False)
    from app.core.config import get_oauth_owner_password_hash

    with pytest.raises(ValueError, match="OAUTH_OWNER_PASSWORD_HASH"):
        get_oauth_owner_password_hash()
