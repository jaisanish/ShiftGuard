"""
ShiftGuard Telemetry Broadcast Service
======================================

WebSocket connection manager and real-time event broadcaster.
Handles multiple frontend clients, cleans up disconnected sockets,
and broadcasts validated telemetry frames in real time.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("shiftguard.broadcast")


class TelemetryBroadcastService:
    """
    Manages active WebSocket client connections and broadcasts
    validated telemetry frames across in-cab consoles and monitors.
    """

    def __init__(self):
        self._active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    @property
    def client_count(self) -> int:
        """Return the number of currently connected listener clients."""
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket, client_type: str = "frontend") -> None:
        """
        Accept an incoming WebSocket connection. Only frontend listeners
        are added to the broadcast fan-out pool.
        """
        await websocket.accept()
        if client_type != "simulator":
            async with self._lock:
                self._active_connections.add(websocket)
        logger.info(
            f"[WEBSOCKET BROADCAST] Registered {client_type} client. "
            f"Active listener connections: {len(self._active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from the broadcast pool.
        """
        async with self._lock:
            self._active_connections.discard(websocket)
        logger.info(
            f"[WEBSOCKET BROADCAST] Disconnected client. "
            f"Active connections: {len(self._active_connections)}"
        )

    async def broadcast_telemetry(self, telemetry_payload: Dict[str, Any]) -> int:
        """
        Broadcast a validated telemetry frame to all connected WebSocket clients.
        Automatically purges any dead or disconnected sockets.

        Returns:
            int: Number of clients that received the broadcast successfully.
        """
        if not self._active_connections:
            return 0

        message_str = json.dumps({
            "type": "telemetry_update",
            "data": telemetry_payload
        })

        dead_connections = set()
        sent_count = 0

        async with self._lock:
            for connection in list(self._active_connections):
                try:
                    await connection.send_text(message_str)
                    sent_count += 1
                except (WebSocketDisconnect, RuntimeError, Exception) as e:
                    logger.debug(f"[WEBSOCKET BROADCAST] Dead socket detected: {e}")
                    dead_connections.add(connection)

            # Purge dead connections
            if dead_connections:
                self._active_connections.difference_update(dead_connections)

        machine_id = telemetry_payload.get("machine_id", "UNKNOWN")
        logger.info(
            f"[WEBSOCKET BROADCAST] Broadcasted telemetry to {sent_count} "
            f"connected frontend clients (machine={machine_id})"
        )
        return sent_count

    async def broadcast_event(self, event_payload: Dict[str, Any]) -> int:
        """
        Broadcast an arbitrary structured JSON event to all connected frontend clients.
        (e.g. safety_update, incident_created, alert_acknowledged).
        """
        if not self._active_connections:
            return 0

        message_str = json.dumps(event_payload)
        dead_connections = set()
        sent_count = 0

        async with self._lock:
            for connection in list(self._active_connections):
                try:
                    await connection.send_text(message_str)
                    sent_count += 1
                except (WebSocketDisconnect, RuntimeError, Exception) as e:
                    logger.debug(f"[WEBSOCKET BROADCAST] Dead socket detected: {e}")
                    dead_connections.add(connection)

            if dead_connections:
                self._active_connections.difference_update(dead_connections)

        event_type = event_payload.get("type", "unknown")
        logger.debug(f"[WEBSOCKET BROADCAST] Broadcasted event '{event_type}' to {sent_count} clients")
        return sent_count


# Global singleton instance
broadcast_service = TelemetryBroadcastService()
