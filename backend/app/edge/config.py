"""
ShiftGuard Edge Safety Engine Configuration
===========================================

Centralized threshold definitions and timing invariants for local deterministic
safety rules. All values are configurable and must not be hardcoded throughout the codebase.

DISCLAIMER:
Thresholds such as the 3.0s seatbelt duration and 5.0m/2.0m proximity limits are
site-policy / prototype demonstration values and do NOT represent a Caterpillar Inc.
safety specification.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyConfig:
    """Deterministic Edge Safety Thresholds and Policy Settings."""

    # Proximity Radar Thresholds (Meters)
    PROXIMITY_WARNING_DISTANCE_M: float = 5.0
    PROXIMITY_CRITICAL_DISTANCE_M: float = 2.0

    # Seatbelt Interlock Duration Thresholds (Seconds)
    # Prototype/site-policy threshold: Unfastened in motion for >= 3.0s emits WARNING
    SEATBELT_VIOLATION_SECONDS: float = 3.0
    # Continued unfastened in motion for >= 6.0s escalates to CRITICAL
    SEATBELT_ESCALATION_SECONDS: float = 6.0

    # Incident Rolling Context Window (Seconds)
    # Target 30-60 seconds pre-event and post-event window
    INCIDENT_BUFFER_SECONDS: float = 60.0

    # Alert State Machine Cooldown & Hysteresis (Seconds)
    ALERT_COOLDOWN_SECONDS: float = 5.0

    # Machine Active Detection Thresholds
    ACTIVE_SPEED_THRESHOLD_KMH: float = 0.5
    ACTIVE_RPM_THRESHOLD: float = 400.0


# Default global configuration instance
safety_config = SafetyConfig()
