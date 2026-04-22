import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException, status


def require_master_auth(x_master_token: Optional[str] = Header(default=None, alias="X-Master-Token")) -> None:
    """
    Minimal API auth guard for internal master endpoints.

    Require callers to provide `X-Master-Token` and compare it with
    `MASTER_API_TOKEN` from environment.
    """
    expected_token = os.getenv("MASTER_API_TOKEN", "").strip()
    if not expected_token:
        # Backward-compatible behavior: if token is not configured,
        # do not block existing internal callers.
        return

    provided_token = (x_master_token or "").strip()
    if not provided_token or not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
        )
