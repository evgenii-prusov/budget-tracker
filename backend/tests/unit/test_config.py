import pytest


def test_get_api_key_returns_value(monkeypatch):
    monkeypatch.setenv("API_KEY", "my-secret")
    from app.core.config import get_api_key

    assert get_api_key() == "my-secret"


def test_get_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    from app.core.config import get_api_key

    with pytest.raises(ValueError, match="API_KEY"):
        get_api_key()
