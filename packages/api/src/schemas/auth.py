"""
Authentication-related Pydantic schemas.
"""

from pydantic import BaseModel


class KeycloakConfigResponse(BaseModel):
    """Keycloak realm configuration for frontend initialization."""

    realm: str
    auth_server_url: str
    client_id: str
    ssl_required: str


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    role: str
    roles: list[str]
    created_at: str | None = None


class UserProfileUpdate(BaseModel):
    """User profile update request."""

    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
