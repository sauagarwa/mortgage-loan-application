"""
Keycloak JWT authentication and RBAC utilities.
"""

import logging
from dataclasses import dataclass
from functools import wraps
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)

# Cache for JWKS keys
_jwks_cache: dict | None = None


@dataclass
class TokenUser:
    """Represents the authenticated user extracted from a JWT token."""

    keycloak_id: str
    email: str
    first_name: str
    last_name: str
    roles: list[str]
    token: str

    @property
    def is_applicant(self) -> bool:
        return "applicant" in self.roles

    @property
    def is_loan_servicer(self) -> bool:
        return "loan_servicer" in self.roles

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    @property
    def primary_role(self) -> str:
        for role in ["admin", "loan_servicer", "applicant"]:
            if role in self.roles:
                return role
        return "applicant"


async def get_jwks() -> dict:
    """Fetch and cache JWKS from Keycloak."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.keycloak_jwks_url, timeout=10.0)
            response.raise_for_status()
            _jwks_cache = response.json()
            return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKS from Keycloak: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


def clear_jwks_cache():
    """Clear the JWKS cache (useful for testing or key rotation)."""
    global _jwks_cache
    _jwks_cache = None


async def decode_token(token: str) -> dict:
    """Decode and validate a JWT token using Keycloak's JWKS."""
    jwks = await get_jwks()

    try:
        # Get the key ID from the token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find the matching key in JWKS
        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if rsa_key is None:
            # Key not found, try refreshing JWKS cache
            clear_jwks_cache()
            jwks = await get_jwks()
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break

        if rsa_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience="account",
            issuer=settings.keycloak_issuer,
            options={"verify_aud": False},
        )
        return payload

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> TokenUser:
    """FastAPI dependency to extract and validate the current user from JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = await decode_token(token)

    # Extract realm roles
    realm_access = payload.get("realm_access", {})
    roles = realm_access.get("roles", [])

    # Also check custom claim if present
    custom_roles = payload.get("realm_roles", [])
    if custom_roles:
        roles = list(set(roles + custom_roles))

    # Filter to only our application roles
    app_roles = [r for r in roles if r in ("applicant", "loan_servicer", "admin")]
    if not app_roles:
        app_roles = ["applicant"]

    return TokenUser(
        keycloak_id=payload.get("sub", ""),
        email=payload.get("email", ""),
        first_name=payload.get("given_name", ""),
        last_name=payload.get("family_name", ""),
        roles=app_roles,
        token=token,
    )


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> TokenUser | None:
    """Like get_current_user but returns None instead of raising if no token."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(allowed_roles: list[str]):
    """Decorator for route handlers that require specific roles.

    Usage:
        @router.get("/admin/users")
        @require_role(["admin"])
        async def list_users(user: TokenUser = Depends(get_current_user)):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the user in kwargs (injected by Depends)
            user = kwargs.get("user") or kwargs.get("current_user")
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            if not any(role in user.roles for role in allowed_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {allowed_roles}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
