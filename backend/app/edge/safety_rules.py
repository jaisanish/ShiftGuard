"""
ShiftGuard Deterministic Edge Safety Rules
==========================================

Implements 100% deterministic, local safety rules for seatbelt interlocks and proximity radar.
Uses configurable thresholds and telemetry-derived timestamps.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from backend.app.edge.config import safety_config
from backend.app.edge.safety_features import is_machine_active
from backend.app.edge.safety_state import AlertSeverity, AlertStatus


def parse_iso(ts_str: str) -> datetime:
    """Parse ISO 8601 string to timezone-aware datetime."""
    try:
        clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return datetime.now(timezone.utc)


@dataclass
class RuleEvaluationResult:
    """Output of evaluating a deterministic safety rule."""
    rule_name: str
    is_violation: bool
    status: AlertStatus
    severity: Optional[AlertSeverity]
    message: str
    evidence: Dict[str, Any]
    should_escalate: bool = False
    is_resolved: bool = False


class SeatbeltSafetyRule:
    """
    Evaluates in-cab operator seatbelt compliance while machine is physically active.

    Deterministic Logic:
    - machine_active == False -> NORMAL (seatbelt unfastened while parked is permitted)
    - machine_active == True AND seatbelt == 'FASTENED' -> NORMAL / RESOLVED
    - machine_active == True AND seatbelt == 'UNFASTENED':
        * Elapsed < SEATBELT_VIOLATION_SECONDS (3.0s) -> DETECTED (transient motion)
        * Elapsed >= 3.0s -> WARNING (audible/visual in-cab warning)
        * Elapsed >= SEATBELT_ESCALATION_SECONDS (6.0s) -> CRITICAL (immediate vehicle speed throttle / alarm)
    """

    def __init__(self):
        # Tracking: machine_id -> start_timestamp_datetime
        self._violation_start: Dict[str, datetime] = {}
        self._current_status: Dict[str, AlertStatus] = {}

    def evaluate(self, telemetry: Dict[str, Any]) -> RuleEvaluationResult:
        machine_id = telemetry.get("machine_id", "UNKNOWN")
        seatbelt = str(telemetry.get("seatbelt_status", "FASTENED")).upper().strip()
        timestamp = parse_iso(telemetry.get("timestamp", ""))
        active = is_machine_active(telemetry)

        # Case 1: Machine not active or seatbelt fastened
        if not active or seatbelt == "FASTENED":
            prev_status = self._current_status.get(machine_id, AlertStatus.NORMAL)
            was_violating = machine_id in self._violation_start
            self._violation_start.pop(machine_id, None)
            self._current_status[machine_id] = AlertStatus.NORMAL

            if was_violating and prev_status in (AlertStatus.WARNING, AlertStatus.CRITICAL, AlertStatus.DETECTED):
                return RuleEvaluationResult(
                    rule_name="SEATBELT",
                    is_violation=False,
                    status=AlertStatus.RESOLVED,
                    severity=None,
                    message="Seatbelt fastened. Interlock secured.",
                    evidence={"seatbelt_status": "FASTENED", "active": active},
                    is_resolved=True,
                )

            return RuleEvaluationResult(
                rule_name="SEATBELT",
                is_violation=False,
                status=AlertStatus.NORMAL,
                severity=None,
                message="Seatbelt compliance nominal.",
                evidence={"seatbelt_status": seatbelt, "active": active},
            )

        # Case 2: Machine active AND seatbelt UNFASTENED
        if machine_id not in self._violation_start:
            self._violation_start[machine_id] = timestamp

        elapsed_sec = max(0.0, (timestamp - self._violation_start[machine_id]).total_seconds())
        evidence = {
            "seatbelt_status": "UNFASTENED",
            "active": True,
            "elapsed_seconds": round(elapsed_sec, 2),
            "speed_kmh": telemetry.get("machine_speed_kmh", 0.0),
            "engine_rpm": telemetry.get("engine_rpm", 0.0),
        }

        # Escalation ladder
        if elapsed_sec >= safety_config.SEATBELT_ESCALATION_SECONDS:
            status = AlertStatus.CRITICAL
            severity = AlertSeverity.CRITICAL
            msg = f"SEATBELT CRITICAL: Unfastened in motion for {elapsed_sec:.1f}s."
            self._current_status[machine_id] = status
            return RuleEvaluationResult(
                rule_name="SEATBELT",
                is_violation=True,
                status=status,
                severity=severity,
                message=msg,
                evidence=evidence,
                should_escalate=True,
            )

        if elapsed_sec >= safety_config.SEATBELT_VIOLATION_SECONDS:
            status = AlertStatus.WARNING
            severity = AlertSeverity.WARNING
            msg = f"SEATBELT WARNING: Operator unfastened while machine active ({elapsed_sec:.1f}s)."
            self._current_status[machine_id] = status
            return RuleEvaluationResult(
                rule_name="SEATBELT",
                is_violation=True,
                status=status,
                severity=severity,
                message=msg,
                evidence=evidence,
            )

        # Elapsed < 3s: DETECTED
        status = AlertStatus.DETECTED
        severity = AlertSeverity.INFO
        msg = f"SEATBELT DETECTED: Unfastened motion initiated ({elapsed_sec:.1f}s)."
        self._current_status[machine_id] = status
        return RuleEvaluationResult(
            rule_name="SEATBELT",
            is_violation=True,
            status=status,
            severity=severity,
            message=msg,
            evidence=evidence,
        )


class ProximitySafetyRule:
    """
    Evaluates obstacle radar proximity and collision risk.

    Deterministic Logic:
    - distance <= PROXIMITY_CRITICAL_DISTANCE_M (2.0m) -> CRITICAL
    - distance <= PROXIMITY_WARNING_DISTANCE_M (5.0m) -> WARNING
    - distance > PROXIMITY_WARNING_DISTANCE_M -> NORMAL / RESOLVED
    """

    def __init__(self):
        # Tracking: machine_id -> previous AlertStatus
        self._current_status: Dict[str, AlertStatus] = {}

    def evaluate(self, telemetry: Dict[str, Any]) -> RuleEvaluationResult:
        machine_id = telemetry.get("machine_id", "UNKNOWN")
        dist = float(telemetry.get("proximity_distance_m", 99.0) or 99.0)
        prev_status = self._current_status.get(machine_id, AlertStatus.NORMAL)

        evidence = {
            "proximity_distance_m": dist,
            "warning_threshold_m": safety_config.PROXIMITY_WARNING_DISTANCE_M,
            "critical_threshold_m": safety_config.PROXIMITY_CRITICAL_DISTANCE_M,
            "speed_kmh": telemetry.get("machine_speed_kmh", 0.0),
            "gps_zone": telemetry.get("gps_zone", "UNKNOWN"),
        }

        # Case 1: Critical distance <= 2.0m
        if dist <= safety_config.PROXIMITY_CRITICAL_DISTANCE_M:
            status = AlertStatus.CRITICAL
            self._current_status[machine_id] = status
            return RuleEvaluationResult(
                rule_name="PROXIMITY",
                is_violation=True,
                status=status,
                severity=AlertSeverity.CRITICAL,
                message=f"CRITICAL PROXIMITY: Obstacle detected at {dist:.1f}m!",
                evidence=evidence,
                should_escalate=(prev_status != AlertStatus.CRITICAL),
            )

        # Case 2: Warning distance <= 5.0m
        if dist <= safety_config.PROXIMITY_WARNING_DISTANCE_M:
            status = AlertStatus.WARNING
            self._current_status[machine_id] = status
            return RuleEvaluationResult(
                rule_name="PROXIMITY",
                is_violation=True,
                status=status,
                severity=AlertSeverity.WARNING,
                message=f"PROXIMITY WARNING: Obstacle detected within {dist:.1f}m.",
                evidence=evidence,
            )

        # Case 3: Clear distance > 5.0m
        self._current_status[machine_id] = AlertStatus.NORMAL
        if prev_status in (AlertStatus.WARNING, AlertStatus.CRITICAL):
            return RuleEvaluationResult(
                rule_name="PROXIMITY",
                is_violation=False,
                status=AlertStatus.RESOLVED,
                severity=None,
                message=f"Proximity clear ({dist:.1f}m). Obstacle cleared.",
                evidence=evidence,
                is_resolved=True,
            )

        return RuleEvaluationResult(
            rule_name="PROXIMITY",
            is_violation=False,
            status=AlertStatus.NORMAL,
            severity=None,
            message=f"Proximity clearance nominal ({dist:.1f}m).",
            evidence=evidence,
        )
