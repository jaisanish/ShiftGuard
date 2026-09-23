"""
ShiftGuard Edge Safety State Machine
====================================

Defines the formal state machine transitions for alerts:
    NORMAL -> DETECTED -> WARNING -> CRITICAL -> ACKNOWLEDGED -> RESOLVED

Provides transition validation and hysteresis / cooldown rules.
"""

from enum import Enum
from typing import Set


class AlertSeverity(str, Enum):
    """Formal alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Formal alert lifecycle states."""
    NORMAL = "NORMAL"
    DETECTED = "DETECTED"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


# Legal transitions allowed in the state machine
VALID_TRANSITIONS = {
    AlertStatus.NORMAL: {AlertStatus.DETECTED, AlertStatus.WARNING, AlertStatus.CRITICAL},
    AlertStatus.DETECTED: {AlertStatus.WARNING, AlertStatus.CRITICAL, AlertStatus.RESOLVED, AlertStatus.NORMAL},
    AlertStatus.WARNING: {AlertStatus.CRITICAL, AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED},
    AlertStatus.CRITICAL: {AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED},
    AlertStatus.ACKNOWLEDGED: {AlertStatus.CRITICAL, AlertStatus.RESOLVED},
    AlertStatus.RESOLVED: {AlertStatus.NORMAL, AlertStatus.DETECTED, AlertStatus.WARNING, AlertStatus.CRITICAL},
}


def is_valid_transition(current: AlertStatus, next_state: AlertStatus) -> bool:
    """Validate whether transitioning from current to next_state is legal."""
    if current == next_state:
        return True
    allowed = VALID_TRANSITIONS.get(current, set())
    return next_state in allowed
