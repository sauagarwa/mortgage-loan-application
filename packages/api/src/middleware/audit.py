"""
Audit logging middleware — automatically logs mutating API requests.
"""

import logging
import re
from typing import Any

from fastapi import Request
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from db import AuditLog, get_db

logger = logging.getLogger(__name__)

# Only log mutating methods
_AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Routes to skip (health checks, auth token refresh, etc.)
_SKIP_PATTERNS = [
    re.compile(r"^/health"),
    re.compile(r"^/docs"),
    re.compile(r"^/openapi"),
    re.compile(r"^/$"),
]

# Map URL patterns to resource types and actions
_RESOURCE_PATTERNS = [
    (re.compile(r"/api/v1/applications/([^/]+)/documents"), "document"),
    (re.compile(r"/api/v1/applications/([^/]+)/decision"), "decision"),
    (re.compile(r"/api/v1/applications/([^/]+)/info-request"), "info_request"),
    (re.compile(r"/api/v1/applications/([^/]+)/risk-assessment"), "risk_assessment"),
    (re.compile(r"/api/v1/applications/([^/]+)"), "application"),
    (re.compile(r"/api/v1/notifications/([^/]+)"), "notification"),
    (re.compile(r"/api/v1/notifications"), "notification"),
    (re.compile(r"/api/v1/servicer"), "servicer"),
    (re.compile(r"/api/v1/loans"), "loan_product"),
    (re.compile(r"/api/v1/auth"), "auth"),
]


def _extract_resource_info(path: str) -> tuple[str, str | None]:
    """Extract resource type and resource ID from the URL path."""
    for pattern, resource_type in _RESOURCE_PATTERNS:
        match = pattern.search(path)
        if match:
            resource_id = match.group(1) if match.lastindex else None
            return resource_type, resource_id
    return "unknown", None


def _derive_action(method: str, path: str, resource_type: str) -> str:
    """Derive a human-readable action from method, path, and resource type."""
    method_action = {
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }
    base = method_action.get(method, method.lower())

    # Special cases
    if "submit" in path:
        return f"submit_{resource_type}"
    if "assign" in path:
        return f"assign_{resource_type}"
    if "mark-all-read" in path:
        return "mark_all_read"
    if "/read" in path and method == "PUT":
        return "mark_read"

    return f"{base}_{resource_type}"


def _extract_user_from_token(request: Request) -> dict[str, Any]:
    """Try to extract user info from the Authorization header without full validation."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return {}

    token = auth_header[7:]
    try:
        payload = jwt.get_unverified_claims(token)
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", [])
        app_roles = [r for r in roles if r in ("applicant", "loan_servicer", "admin")]
        primary_role = "applicant"
        for role in ["admin", "loan_servicer", "applicant"]:
            if role in app_roles:
                primary_role = role
                break

        return {
            "keycloak_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": primary_role,
        }
    except Exception:
        return {}


def _get_client_ip(request: Request) -> str | None:
    """Get the client's IP address, checking X-Forwarded-For first."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs mutating API requests to the audit_log table."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip non-mutating methods
        if request.method not in _AUDITED_METHODS:
            return await call_next(request)

        # Skip excluded paths
        path = request.url.path
        for pattern in _SKIP_PATTERNS:
            if pattern.match(path):
                return await call_next(request)

        # Process the request
        response = await call_next(request)

        # Only log successful mutations (2xx status codes)
        if 200 <= response.status_code < 300:
            try:
                await self._log_audit_entry(request, response)
            except Exception:
                logger.exception("Failed to write audit log entry")

        return response

    async def _log_audit_entry(self, request: Request, response: Response) -> None:
        """Write an audit log entry for a successful mutation."""
        path = request.url.path
        resource_type, resource_id = _extract_resource_info(path)
        action = _derive_action(request.method, path, resource_type)
        user_info = _extract_user_from_token(request)
        client_ip = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Look up user_id from keycloak_id
        from sqlalchemy import select

        from db import User

        user_id = None
        keycloak_id = user_info.get("keycloak_id")

        async for session in get_db():
            if keycloak_id:
                result = await session.execute(
                    select(User.id).where(User.keycloak_id == keycloak_id)
                )
                row = result.scalar_one_or_none()
                if row:
                    user_id = row

            entry = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id if resource_id else None,
                user_id=user_id,
                user_email=user_info.get("email"),
                user_role=user_info.get("role"),
                details={
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "query_params": dict(request.query_params),
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
            session.add(entry)
            await session.commit()
            break
