"""
WebSocket endpoints for real-time updates.

- /ws/applications/{application_id} — application status & agent progress
- /ws/servicer/notifications — servicer alerts
"""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..core.security import decode_token
from ..services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


async def _authenticate_ws(websocket: WebSocket, token: str | None) -> dict | None:
    """Validate JWT token for WebSocket connections. Returns payload or None."""
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return None
    try:
        payload = await decode_token(token)
        return payload
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return None


def _get_app_roles(payload: dict) -> list[str]:
    """Extract application roles from JWT payload."""
    realm_access = payload.get("realm_access", {})
    roles = realm_access.get("roles", [])
    custom_roles = payload.get("realm_roles", [])
    if custom_roles:
        roles = list(set(roles + custom_roles))
    return [r for r in roles if r in ("applicant", "loan_servicer", "admin")]


@router.websocket("/applications/{application_id}")
async def ws_application_updates(
    websocket: WebSocket,
    application_id: str,
    token: str = Query(default=""),
) -> None:
    """WebSocket for real-time application status and agent progress updates."""
    payload = await _authenticate_ws(websocket, token or None)
    if payload is None:
        return

    channel = f"application:{application_id}"
    await manager.connect(websocket, channel)

    try:
        # Send initial connected message
        await websocket.send_json({
            "type": "connected",
            "data": {"application_id": application_id},
        })

        # Keep connection alive, listen for client pings
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, channel)


@router.websocket("/servicer/notifications")
async def ws_servicer_notifications(
    websocket: WebSocket,
    token: str = Query(default=""),
) -> None:
    """WebSocket for servicer real-time notifications (new apps, info responses)."""
    payload = await _authenticate_ws(websocket, token or None)
    if payload is None:
        return

    roles = _get_app_roles(payload)
    if "loan_servicer" not in roles and "admin" not in roles:
        await websocket.close(code=4003, reason="Insufficient permissions")
        return

    channel = "servicer:notifications"
    await manager.connect(websocket, channel)

    try:
        await websocket.send_json({
            "type": "connected",
            "data": {"role": "servicer"},
        })

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, channel)
