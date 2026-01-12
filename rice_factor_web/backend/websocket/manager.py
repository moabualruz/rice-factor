"""WebSocket connection manager for real-time updates.

Manages WebSocket connections and broadcasts events to all connected clients.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from rice_factor_web.backend.websocket.events import WebSocketEvent

if TYPE_CHECKING:
    from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for real-time updates.

    Thread-safe connection management with broadcast capabilities.
    Supports multiple concurrent connections.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._active_connections: list["WebSocket"] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: "WebSocket") -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register.
        """
        await websocket.accept()
        async with self._lock:
            self._active_connections.append(websocket)

    async def disconnect(self, websocket: "WebSocket") -> None:
        """Remove a WebSocket connection from the active list.

        Args:
            websocket: The WebSocket connection to remove.
        """
        async with self._lock:
            if websocket in self._active_connections:
                self._active_connections.remove(websocket)

    async def broadcast(self, event: WebSocketEvent) -> None:
        """Broadcast an event to all connected clients.

        Args:
            event: The event to broadcast.
        """
        message = event.to_json()
        disconnected: list["WebSocket"] = []

        async with self._lock:
            for connection in self._active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Connection is likely closed
                    disconnected.append(connection)

            # Clean up disconnected clients
            for ws in disconnected:
                if ws in self._active_connections:
                    self._active_connections.remove(ws)

    async def send_to(self, websocket: "WebSocket", event: WebSocketEvent) -> bool:
        """Send an event to a specific connection.

        Args:
            websocket: The target WebSocket connection.
            event: The event to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            await websocket.send_text(event.to_json())
            return True
        except Exception:
            await self.disconnect(websocket)
            return False

    @property
    def connection_count(self) -> int:
        """Get the number of active connections.

        Returns:
            Number of currently connected clients.
        """
        return len(self._active_connections)

    async def websocket_endpoint(self, websocket: "WebSocket") -> None:
        """WebSocket endpoint handler.

        Accepts connection, keeps it alive, and handles disconnection.
        Can be extended to handle client messages for subscriptions.

        Args:
            websocket: The WebSocket connection.
        """
        await self.connect(websocket)
        try:
            while True:
                # Wait for client messages (keepalive or commands)
                data = await websocket.receive_text()
                # Could handle client commands here:
                # - subscribe to specific artifact IDs
                # - change notification preferences
                # For now, just acknowledge
                if data == "ping":
                    await websocket.send_text("pong")
        except Exception:
            # Connection closed (client disconnect or error)
            pass
        finally:
            await self.disconnect(websocket)


# Global connection manager instance
ws_manager = ConnectionManager()
