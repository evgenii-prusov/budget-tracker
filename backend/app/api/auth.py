from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_api_key

_bearer_scheme = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(_bearer_scheme),
    ] = None,
) -> None:
    expected = get_api_key()
    if credentials is None or credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
