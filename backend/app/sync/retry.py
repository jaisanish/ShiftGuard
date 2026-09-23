"""
ShiftGuard Exponential Backoff Retry Policy
===========================================
"""

from datetime import datetime, timezone, timedelta


def calculate_next_retry_iso(
    retry_count: int,
    base_seconds: float = 2.0,
    max_seconds: float = 60.0,
) -> str:
    """
    Calculate next retry timestamp in ISO 8601 UTC using exponential backoff:
    delay = min(max_seconds, base_seconds * (2 ** retry_count))
    """
    delay = min(max_seconds, base_seconds * (2 ** retry_count))
    next_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
    return next_time.isoformat().replace("+00:00", "Z")
