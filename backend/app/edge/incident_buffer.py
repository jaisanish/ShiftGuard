"""
ShiftGuard Rolling In-Memory Telemetry Context Buffer
=====================================================

Maintains a sliding 30-60 second telemetry buffer per machine to capture
rich contextual snapshots whenever an incident is declared:
    [PRE-EVENT TELEMETRY] + [TRIGGER EVENT] + [POST-EVENT TELEMETRY]
"""

from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.edge.config import safety_config


def parse_iso_timestamp(ts_str: str) -> datetime:
    """Parse ISO 8601 string to datetime."""
    try:
        clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return datetime.now(timezone.utc)


class IncidentContextBuffer:
    """
    Maintains sliding window telemetry queues for machines and builds
    structured pre/trigger/post incident context records.
    """

    def __init__(self, max_seconds: float = safety_config.INCIDENT_BUFFER_SECONDS):
        self.max_seconds = max_seconds
        # Mapping: machine_id -> deque of telemetry dicts
        self._buffers: Dict[str, deque] = {}

    def append(self, telemetry_frame: Dict[str, Any]) -> None:
        """Add a validated telemetry frame to the machine's rolling buffer."""
        machine_id = telemetry_frame.get("machine_id", "DEFAULT")
        if machine_id not in self._buffers:
            self._buffers[machine_id] = deque()

        q = self._buffers[machine_id]
        q.append(dict(telemetry_frame))

        # Evict records older than max_seconds relative to the latest frame
        latest_ts = parse_iso_timestamp(telemetry_frame.get("timestamp", ""))
        while q:
            oldest_ts = parse_iso_timestamp(q[0].get("timestamp", ""))
            delta_sec = (latest_ts - oldest_ts).total_seconds()
            if delta_sec > self.max_seconds:
                q.popleft()
            else:
                break

    def get_recent_frames(self, machine_id: str) -> List[Dict[str, Any]]:
        """Return all frames currently in the rolling window for a machine."""
        q = self._buffers.get(machine_id)
        if not q:
            return []
        return list(q)

    def capture_context(
        self,
        machine_id: str,
        trigger_frame: Dict[str, Any],
        pre_event_seconds: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Capture pre-event context leading up to a trigger frame.

        Returns:
            Dict containing 'pre_event', 'trigger_event', and an empty 'post_event' list
            ready to accumulate incoming frames until resolution.
        """
        frames = self.get_recent_frames(machine_id)
        trigger_ts = parse_iso_timestamp(trigger_frame.get("timestamp", ""))

        pre_event = []
        for f in frames:
            f_ts = parse_iso_timestamp(f.get("timestamp", ""))
            # Frames strictly before trigger, within pre_event_seconds
            if f_ts < trigger_ts and (trigger_ts - f_ts).total_seconds() <= pre_event_seconds:
                pre_event.append(f)

        return {
            "pre_event": pre_event,
            "trigger_event": dict(trigger_frame),
            "post_event": [],
        }


# Global singleton instance
incident_context_buffer = IncidentContextBuffer()
