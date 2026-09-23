"""
ShiftGuard Edge Safety Kinematic Feature Extraction
===================================================

Provides centralized extraction and interpretation of machine state and physical activity.
Prevents duplicated active-machine calculations across multiple modules.
"""

from typing import Any, Dict, Union
from backend.app.edge.config import safety_config


ACTIVE_OPERATING_STATES = {
    "WORKING",
    "TRAVELLING",
    "HAULING_LOADED",
    "RETURN_EMPTY",
    "SPOTTING",
    "DIGGING",
    "LOADING",
    "DUMPING",
}


def is_machine_active(telemetry: Union[Dict[str, Any], Any]) -> bool:
    """
    Centralized determination of whether the machine is physically active.

    A machine is considered ACTIVE if:
    1. Ground speed exceeds the motion threshold (> 0.5 km/h), OR
    2. Engine RPM exceeds the active threshold (> 400 RPM) while in an active operating state, OR
    3. Operating state is explicitly designated as active haulage / duty cycle work.

    Returns:
        bool: True if machine is active/in-motion, False if stopped or parked.
    """
    if isinstance(telemetry, dict):
        speed = float(telemetry.get("machine_speed_kmh", 0.0) or 0.0)
        rpm = float(telemetry.get("engine_rpm", 0.0) or 0.0)
        raw_state = str(telemetry.get("operating_state", "IDLE") or "IDLE").upper().strip()
    else:
        speed = float(getattr(telemetry, "machine_speed_kmh", 0.0) or 0.0)
        rpm = float(getattr(telemetry, "engine_rpm", 0.0) or 0.0)
        raw_state = str(getattr(telemetry, "operating_state", "IDLE") or "IDLE").upper().strip()

    # Rule 1: Clear ground motion
    if speed >= safety_config.ACTIVE_SPEED_THRESHOLD_KMH:
        return True

    # Rule 2: Active operating state with running engine
    if raw_state in ACTIVE_OPERATING_STATES and rpm >= safety_config.ACTIVE_RPM_THRESHOLD:
        return True

    return False


def to_canonical_operating_state(
    raw_state: Any, speed_kmh: float = 0.0, engine_rpm: float = 0.0
) -> str:
    """
    Map raw operating state codes (e.g. HAULING_LOADED, SPOTTING) to the
    4 canonical kinematic states required by the operator console:
        - IDLE
        - WORKING
        - TRAVELLING
        - STOPPED
    """
    s = str(raw_state or "").upper().strip()
    if s in ("IDLE", "WORKING", "TRAVELLING", "STOPPED"):
        if s in ("IDLE", "STOPPED") and speed_kmh >= 1.0:
            return "TRAVELLING"
        if s == "STOPPED" and engine_rpm > 300.0 and speed_kmh < 1.0:
            return "IDLE"
        return s

    if s in ("HAULING_LOADED", "HAULING_EMPTY", "HAULING", "RETURN_EMPTY"):
        return "TRAVELLING" if speed_kmh >= 1.0 else "WORKING"

    if s in ("SPOTTING", "LOADING", "DUMPING", "EXCAVATING", "DOZING"):
        return "TRAVELLING" if speed_kmh >= 15.0 else "WORKING"

    if speed_kmh >= 1.0:
        return "TRAVELLING"
    if engine_rpm > 300.0:
        return "IDLE"
    return "STOPPED"

