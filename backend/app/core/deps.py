"""
WebGuard RF - FastAPI Dependencies
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .security import decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Extract and validate JWT from Authorization header."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return {"sub": payload.get("sub"), "role": payload.get("role", "researcher")}


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Optional auth - returns None if no valid token."""
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    return {"sub": payload.get("sub"), "role": payload.get("role", "researcher")}


def require_role(*allowed: str):
    """Dependency that checks user role."""

    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _check
