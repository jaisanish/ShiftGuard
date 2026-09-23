"""
ShiftGuard Simulator WebSocket Client
=====================================

Resilient WebSocket client for transmitting simulated telemetry streams
to the FastAPI edge ingestion service (/ws/telemetry).
Features:
- Automatic reconnect with exponential backoff.
- Precise pacing control (speed multiplier).
- Standardized logging with [SIMULATOR] tags.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger("shiftguard.simulator.client")


class SimulatorClient:
    """
    WebSocket client that streams telemetry frames to the ShiftGuard Edge backend.
    """

    def __init__(
        self,
        url: str = "ws://127.0.0.1:8000/ws/telemetry?role=simulator",
        max_reconnect_attempts: int = 10,
        initial_backoff_sec: float = 1.0,
        max_backoff_sec: float = 10.0,
    ):
        self.url = url
        self.max_reconnect_attempts = max_reconnect_attempts
        self.initial_backoff_sec = initial_backoff_sec
        self.max_backoff_sec = max_backoff_sec
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False

    async def connect(self) -> bool:
        """
        Attempt connection to edge WebSocket endpoint with exponential backoff.
        """
        backoff = self.initial_backoff_sec
        for attempt in range(1, self.max_reconnect_attempts + 1):
            try:
                print(f"[SIMULATOR] Connecting to edge WebSocket: {self.url} (attempt {attempt})...")
                self._ws = await websockets.connect(self.url)
                print(f"[SIMULATOR] Connected successfully to edge ingestion service at {self.url}")
                return True
            except (OSError, websockets.WebSocketException) as e:
                print(f"[SIMULATOR] Connection failed ({e}). Retrying in {backoff:.1f}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.5, self.max_backoff_sec)

        print(f"[SIMULATOR] Exceeded maximum connection attempts ({self.max_reconnect_attempts}).")
        return False

    async def send_frame(self, telemetry_frame: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a single telemetry frame and await acknowledgement.
        """
        if not self._ws:
            connected = await self.connect()
            if not connected:
                raise ConnectionError("Unable to establish WebSocket connection.")

        payload_json = json.dumps(telemetry_frame)
        try:
            await self._ws.send(payload_json)
            ack_raw = await self._ws.recv()
            ack = json.loads(ack_raw)

            machine_id = telemetry_frame.get("machine_id", "UNKNOWN")
            state = telemetry_frame.get("operating_state", "UNKNOWN")
            fault = telemetry_frame.get("fault_code", "NONE")
            speed = telemetry_frame.get("machine_speed_kmh", 0.0)
            status = ack.get("status", "unknown")

            print(
                f"[SIMULATOR] Transmitted telemetry: machine={machine_id} state={state} "
                f"speed={speed}km/h fault={fault} -> Server Ack: status={status}"
            )
            return ack

        except ConnectionClosed as cc:
            print(f"[SIMULATOR] Connection closed unexpectedly by server: {cc}. Resetting socket.")
            self._ws = None
            return None

    async def close(self):
        """Cleanly close connection."""
        if self._ws:
            print("[SIMULATOR] Closing simulator WebSocket connection.")
            await self._ws.close()
            self._ws = None
