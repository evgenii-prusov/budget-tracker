import os

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

os.environ["API_KEY"] = "test-secret"

from app.api.auth import verify_api_key  # noqa: E402


def test_verify_api_key_valid_token():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-secret")
    verify_api_key(credentials)  # should not raise


def test_verify_api_key_wrong_token():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-token")
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(credentials)
    assert exc_info.value.status_code == 401


def test_verify_api_key_no_credentials():
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(None)
    assert exc_info.value.status_code == 401


def test_verify_api_key_401_has_www_authenticate_header():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad")
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(credentials)
    assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"
