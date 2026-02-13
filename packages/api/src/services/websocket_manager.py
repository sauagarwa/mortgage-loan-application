"""
WebSocket connection manager with Redis pub/sub for cross-process messaging.

Manages two channel types:
- application:{application_id} — progress updates for a specific application
- servicer:notifications — alerts for loan servicers
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis

from ..core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and Redis pub/sub subscriptions."""

    def __init__(self) -> None:
        # channel -> set of connected websockets
        self._connections: dict[str, set[WebSocket]] = {}
        self._redis: Redis | None = None
        self._pubsub_task: asyncio.Task | None = None

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def start(self) -> None:
        """Start the Redis pub/sub listener."""
        if self._pubsub_task is None:
            self._pubsub_task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        """Stop the pub/sub listener and close connections."""
        if self._pubsub_task:
            self._pubsub_task.cancel()
            self._pubsub_task = None
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept a WebSocket connection and subscribe to a channel."""
        await websocket.accept()
        if channel not in self._connections:
            self._connections[channel] = set()
        self._connections[channel].add(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Remove a WebSocket from a channel."""
        if channel in self._connections:
            self._connections[channel].discard(websocket)
            if not self._connections[channel]:
                del self._connections[channel]
        logger.info(f"WebSocket disconnected from channel: {channel}")

    async def broadcast_local(self, channel: str, message: dict[str, Any]) -> None:
        """Send a message to all local WebSocket connections on a channel."""
        if channel not in self._connections:
            return

        dead: list[WebSocket] = []
        data = json.dumps(message)
        for ws in self._connections[channel]:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._connections[channel].discard(ws)

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        """Publish a message via Redis pub/sub (for cross-process delivery)."""
        redis = await self._get_redis()
        payload = json.dumps({"channel": channel, "message": message})
        await redis.publish("ws:broadcast", payload)

    async def _listen(self) -> None:
        """Listen for Redis pub/sub messages and forward to local WebSockets."""
        while True:
            try:
                redis = await self._get_redis()
                pubsub = redis.pubsub()
                await pubsub.subscribe("ws:broadcast")

                async for raw_message in pubsub.listen():
                    if raw_message["type"] != "message":
                        continue
                    try:
                        payload = json.loads(raw_message["data"])
                        channel = payload["channel"]
                        message = payload["message"]
                        await self.broadcast_local(channel, message)
                    except (json.JSONDecodeError, KeyError):
                        logger.warning("Invalid pub/sub message received")

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Redis pub/sub listener error, reconnecting...")
                await asyncio.sleep(2)


# Singleton instance
manager = ConnectionManager()


async def publish_event(channel: str, message: dict[str, Any]) -> None:
    """Convenience function to publish an event from anywhere in the app."""
    try:
        await manager.publish(channel, message)
    except Exception:
        logger.exception(f"Failed to publish event to {channel}")


def publish_event_sync(channel: str, message: dict[str, Any]) -> None:
    """Synchronous version for use in Celery tasks — publishes via Redis directly."""
    import redis as sync_redis

    try:
        r = sync_redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        payload = json.dumps({"channel": channel, "message": message})
        r.publish("ws:broadcast", payload)
        r.close()
    except Exception:
        logger.exception(f"Failed to publish sync event to {channel}")
