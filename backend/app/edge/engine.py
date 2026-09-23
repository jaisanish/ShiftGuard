"""
ShiftGuard Edge Safety Engine
=============================

100% Deterministic Local Rule Orchestrator.
Evaluates seatbelt and proximity radar rules on every telemetry tick,
manages alert lifecycles in SQLite, captures sliding incident context buffers,
and provides authoritative safety states for the operator console.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.database.models import AlertModel, IncidentModel, utc_now_iso
from backend.app.edge.incident_buffer import incident_context_buffer
from backend.app.edge.safety_rules import (
    ProximitySafetyRule,
    RuleEvaluationResult,
    SeatbeltSafetyRule,
)
from backend.app.edge.safety_state import AlertSeverity, AlertStatus

logger = logging.getLogger("shiftguard.edge_engine")


class EdgeSafetyEngine:
    """
    Deterministic Edge Safety Engine executing local rules on every telemetry frame.
    Guarantees zero reliance on cloud or ML models for immediate cab safety.
    """

    def __init__(self):
        # Per-machine deterministic rule evaluators
        self._seatbelt_rules: Dict[str, SeatbeltSafetyRule] = {}
        self._proximity_rules: Dict[str, ProximitySafetyRule] = {}
        # Active incident tracking: (machine_id, incident_type) -> incident_id
        self._open_incidents: Dict[Tuple[str, str], str] = {}
        # Active alert tracking: (machine_id, alert_type) -> alert_id
        self._active_alerts: Dict[Tuple[str, str], str] = {}

    def _get_seatbelt_rule(self, machine_id: str) -> SeatbeltSafetyRule:
        if machine_id not in self._seatbelt_rules:
            self._seatbelt_rules[machine_id] = SeatbeltSafetyRule()
        return self._seatbelt_rules[machine_id]

    def _get_proximity_rule(self, machine_id: str) -> ProximitySafetyRule:
        if machine_id not in self._proximity_rules:
            self._proximity_rules[machine_id] = ProximitySafetyRule()
        return self._proximity_rules[machine_id]

    def evaluate_telemetry(
        self, db: Session, telemetry_frame: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a single telemetry frame across all deterministic safety rules.

        Returns:
            Dict containing:
                - machine_id
                - safety_state ('NORMAL', 'WARNING', 'CRITICAL')
                - seatbelt_status
                - proximity_distance_m
                - active_alerts (list of alert dicts)
                - is_critical (bool)
                - critical_alert (dict or None)
                - new_incident (dict or None if an incident was created)
        """
        machine_id = telemetry_frame.get("machine_id", "CAT-797F-102")
        operator_id = telemetry_frame.get("operator_id", "OP-101")
        task_id = telemetry_frame.get("task_id", "UNKNOWN")
        timestamp = telemetry_frame.get("timestamp", utc_now_iso())
        gps_zone = telemetry_frame.get("gps_zone", "UNKNOWN")
        proximity_dist = float(telemetry_frame.get("proximity_distance_m", 40.0) or 40.0)
        seatbelt_val = str(telemetry_frame.get("seatbelt_status", "FASTENED")).upper().strip()

        # 1. Append frame to rolling 60-second context buffer
        incident_context_buffer.append(telemetry_frame)

        # 2. Evaluate Seatbelt Safety Rule
        seatbelt_rule = self._get_seatbelt_rule(machine_id)
        seatbelt_res: RuleEvaluationResult = seatbelt_rule.evaluate(telemetry_frame)

        # 3. Evaluate Proximity Safety Rule
        proximity_rule = self._get_proximity_rule(machine_id)
        proximity_res: RuleEvaluationResult = proximity_rule.evaluate(telemetry_frame)

        rule_results = [seatbelt_res, proximity_res]
        new_incident_payload = None

        created_or_updated_alerts = []
        created_incidents = []

        # 4. Process each rule evaluation in SQLite
        for res in rule_results:
            alert_key = (machine_id, res.rule_name)
            incident_key = (machine_id, res.rule_name)

            # Case A: Violation active (WARNING or CRITICAL)
            if res.is_violation and res.severity in (AlertSeverity.WARNING, AlertSeverity.CRITICAL):
                alert_record = db.execute(
                    select(AlertModel).where(
                        AlertModel.machine_id == machine_id,
                        AlertModel.alert_type == res.rule_name,
                        AlertModel.status.in_(["ACTIVE", "ACKNOWLEDGED"]),
                    )
                ).scalar_one_or_none()

                if alert_record:
                    # Update existing active alert
                    alert_record.severity = res.severity.value
                    alert_record.message = res.message
                    alert_record.evidence = json.dumps(res.evidence)
                    alert_record.timestamp = timestamp
                    created_or_updated_alerts.append(alert_record)
                else:
                    # Create new alert record
                    new_alert_id = str(uuid.uuid4())
                    title = f"{res.rule_name} HAZARD" if res.severity == AlertSeverity.CRITICAL else f"{res.rule_name} WARNING"
                    alert_record = AlertModel(
                        id=new_alert_id,
                        timestamp=timestamp,
                        machine_id=machine_id,
                        operator_id=operator_id,
                        task_id=task_id,
                        alert_type=res.rule_name,
                        severity=res.severity.value,
                        status="ACTIVE",
                        source="EDGE",
                        code=telemetry_frame.get("fault_code", "NONE"),
                        title=title,
                        message=res.message,
                        evidence=json.dumps(res.evidence),
                        created_at=timestamp,
                        acknowledged=False,
                    )
                    db.add(alert_record)
                    created_or_updated_alerts.append(alert_record)

                # If Critical Severity: Trigger or escalate Incident
                if res.severity == AlertSeverity.CRITICAL:
                    open_incident = db.execute(
                        select(IncidentModel).where(
                            IncidentModel.machine_id == machine_id,
                            IncidentModel.incident_type == res.rule_name,
                            IncidentModel.status == "OPEN",
                        )
                    ).scalar_one_or_none()

                    if not open_incident:
                        # Capture rich context: 30s pre-event + trigger
                        context_dict = incident_context_buffer.capture_context(
                            machine_id, telemetry_frame, pre_event_seconds=30.0
                        )
                        inc_id = str(uuid.uuid4())
                        new_incident = IncidentModel(
                            id=inc_id,
                            machine_id=machine_id,
                            operator_id=operator_id,
                            task_id=task_id,
                            alert_id=alert_record.id,
                            incident_type=res.rule_name,
                            severity="CRITICAL",
                            summary=res.message,
                            evidence=json.dumps(res.evidence),
                            context_buffer=json.dumps(context_dict),
                            started_at=timestamp,
                            triggered_at=timestamp,
                            status="OPEN",
                            gps_zone=gps_zone,
                            timestamp=timestamp,
                        )
                        db.add(new_incident)
                        created_incidents.append(new_incident)

                        new_incident_payload = {
                            "id": inc_id,
                            "machine_id": machine_id,
                            "operator_id": operator_id,
                            "task_id": task_id,
                            "incident_type": res.rule_name,
                            "severity": "CRITICAL",
                            "summary": res.message,
                            "proximity_distance_m": proximity_dist,
                            "triggered_at": timestamp,
                            "status": "OPEN",
                            "gps_zone": gps_zone,
                        }
                        logger.warning(
                            f"[EDGE SAFETY ENGINE] New CRITICAL incident created: {inc_id} "
                            f"({res.rule_name}) for machine {machine_id}"
                        )

            # Case B: Rule Resolved
            elif res.is_resolved:
                resolved_alert = db.execute(
                    select(AlertModel).where(
                        AlertModel.machine_id == machine_id,
                        AlertModel.alert_type == res.rule_name,
                        AlertModel.status.in_(["ACTIVE", "ACKNOWLEDGED"]),
                    )
                ).scalar_one_or_none()
                if resolved_alert:
                    resolved_alert.status = "RESOLVED"
                    resolved_alert.resolved_at = timestamp

                # Close open incident if any
                open_inc = db.execute(
                    select(IncidentModel).where(
                        IncidentModel.machine_id == machine_id,
                        IncidentModel.incident_type == res.rule_name,
                        IncidentModel.status == "OPEN",
                    )
                ).scalar_one_or_none()
                if open_inc:
                    open_inc.status = "RESOLVED"
                    open_inc.resolved_at = timestamp
                    # Update context buffer with post_event frames
                    try:
                        ctx = json.loads(open_inc.context_buffer or "{}")
                        post_frames = incident_context_buffer.get_recent_frames(machine_id)
                        ctx["post_event"] = post_frames[-10:] if post_frames else []
                        open_inc.context_buffer = json.dumps(ctx)
                    except Exception as e:
                        logger.debug(f"Failed to update post-event context buffer: {e}")

        db.commit()

        # Local-First Ordering: Enqueue committed alerts and incidents into sync_outbox
        for a in created_or_updated_alerts:
            try:
                from backend.app.sync.event_serializer import serialize_alert_event
                from backend.app.sync.outbox import OutboxService
                OutboxService.enqueue_event(db, "ALERT", serialize_alert_event(a), event_id=a.id)
            except Exception as e:
                logger.warning(f"[OUTBOX] Failed to enqueue alert: {e}")

        for inc in created_incidents:
            try:
                from backend.app.sync.event_serializer import serialize_incident_event
                from backend.app.sync.outbox import OutboxService
                OutboxService.enqueue_event(db, "INCIDENT", serialize_incident_event(inc), event_id=inc.id)
            except Exception as e:
                logger.warning(f"[OUTBOX] Failed to enqueue incident: {e}")

        # 5. Compile active alerts for this machine
        active_db_alerts = db.execute(
            select(AlertModel)
            .where(AlertModel.machine_id == machine_id, AlertModel.status.in_(["ACTIVE", "ACKNOWLEDGED"]))
            .order_by(desc(AlertModel.timestamp))
        ).scalars().all()

        active_alerts_list = []
        is_critical = False
        critical_alert_dict = None

        for a in active_db_alerts:
            evidence_dict = {}
            if a.evidence:
                try:
                    evidence_dict = json.loads(a.evidence)
                except Exception:
                    evidence_dict = {}

            alert_dict = {
                "id": a.id,
                "timestamp": a.timestamp,
                "machine_id": a.machine_id,
                "operator_id": a.operator_id,
                "task_id": a.task_id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "status": a.status,
                "source": a.source,
                "code": a.code,
                "title": a.title,
                "message": a.message,
                "evidence": evidence_dict,
                "created_at": a.created_at,
                "resolved_at": a.resolved_at,
                "acknowledged": a.acknowledged,
                "acknowledged_at": a.acknowledged_at,
            }
            active_alerts_list.append(alert_dict)

            if a.severity == "CRITICAL" and not a.acknowledged:
                is_critical = True
                if critical_alert_dict is None:
                    critical_alert_dict = alert_dict

        # Determine overall safety state
        if is_critical or any(a["severity"] == "CRITICAL" for a in active_alerts_list):
            overall_state = "CRITICAL"
        elif any(a["severity"] == "WARNING" for a in active_alerts_list):
            overall_state = "WARNING"
        else:
            overall_state = "NORMAL"

        return {
            "machine_id": machine_id,
            "safety_state": overall_state,
            "seatbelt_status": seatbelt_val,
            "proximity_distance_m": proximity_dist,
            "active_alerts": active_alerts_list,
            "is_critical": is_critical,
            "critical_alert": critical_alert_dict,
            "new_incident": new_incident_payload,
        }

    def acknowledge_alert(self, db: Session, alert_id: str, operator_id: str = "OP-101") -> Optional[Dict[str, Any]]:
        """Acknowledge an active alert by ID."""
        alert = db.execute(
            select(AlertModel).where(AlertModel.id == alert_id)
        ).scalar_one_or_none()

        if not alert:
            return None

        now = utc_now_iso()
        alert.acknowledged = True
        alert.acknowledged_at = now
        alert.status = "ACKNOWLEDGED"
        db.commit()

        # Also acknowledge any linked incident
        inc = db.execute(
            select(IncidentModel).where(IncidentModel.alert_id == alert_id)
        ).scalar_one_or_none()
        if inc and inc.status == "OPEN":
            inc.status = "ACKNOWLEDGED"
            db.commit()

        # Local-First Ordering: Enqueue alert acknowledgment to sync_outbox
        try:
            from backend.app.sync.event_serializer import serialize_alert_event
            from backend.app.sync.outbox import OutboxService
            import time
            OutboxService.enqueue_event(
                db,
                "ALERT_ACKNOWLEDGED",
                serialize_alert_event(alert),
                event_id=f"ack-alert-{alert.id}-{int(time.time())}",
            )
        except Exception as e:
            logger.warning(f"[OUTBOX] Failed to enqueue alert acknowledgment: {e}")

        logger.info(f"[EDGE SAFETY ENGINE] Alert {alert_id} acknowledged by operator {operator_id}")
        return {
            "id": alert.id,
            "machine_id": alert.machine_id,
            "acknowledged": True,
            "acknowledged_at": now,
        }

    def acknowledge_incident(self, db: Session, incident_id: str, operator_id: str = "OP-101") -> Optional[Dict[str, Any]]:
        """Acknowledge an incident by ID."""
        inc = db.execute(
            select(IncidentModel).where(IncidentModel.id == incident_id)
        ).scalar_one_or_none()

        if not inc:
            return None

        inc.status = "ACKNOWLEDGED"
        now = utc_now_iso()
        db.commit()

        # Local-First Ordering: Enqueue incident acknowledgment to sync_outbox
        try:
            from backend.app.sync.event_serializer import serialize_incident_event
            from backend.app.sync.outbox import OutboxService
            import time
            OutboxService.enqueue_event(
                db,
                "INCIDENT_ACKNOWLEDGED",
                serialize_incident_event(inc),
                event_id=f"ack-inc-{inc.id}-{int(time.time())}",
            )
        except Exception as e:
            logger.warning(f"[OUTBOX] Failed to enqueue incident acknowledgment: {e}")

        # Acknowledge linked alert if any
        if inc.alert_id:
            self.acknowledge_alert(db, inc.alert_id, operator_id)

        logger.info(f"[EDGE SAFETY ENGINE] Incident {incident_id} acknowledged by operator {operator_id}")
        return {
            "id": inc.id,
            "machine_id": inc.machine_id,
            "status": "ACKNOWLEDGED",
            "acknowledged_at": now,
        }

    def get_safety_state(self, db: Session, machine_id: str) -> Dict[str, Any]:
        """Query current safety state snapshot for a machine."""
        active_db_alerts = db.execute(
            select(AlertModel)
            .where(AlertModel.machine_id == machine_id, AlertModel.status.in_(["ACTIVE", "ACKNOWLEDGED"]))
            .order_by(desc(AlertModel.timestamp))
        ).scalars().all()

        active_alerts_list = []
        is_critical = False
        critical_alert_dict = None

        for a in active_db_alerts:
            evidence_dict = {}
            if a.evidence:
                try:
                    evidence_dict = json.loads(a.evidence)
                except Exception:
                    evidence_dict = {}

            alert_dict = {
                "id": a.id,
                "timestamp": a.timestamp,
                "machine_id": a.machine_id,
                "operator_id": a.operator_id,
                "task_id": a.task_id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "status": a.status,
                "source": a.source,
                "code": a.code,
                "title": a.title,
                "message": a.message,
                "evidence": evidence_dict,
                "created_at": a.created_at,
                "resolved_at": a.resolved_at,
                "acknowledged": a.acknowledged,
                "acknowledged_at": a.acknowledged_at,
            }
            active_alerts_list.append(alert_dict)

            if a.severity == "CRITICAL" and not a.acknowledged:
                is_critical = True
                if critical_alert_dict is None:
                    critical_alert_dict = alert_dict

        if is_critical or any(a["severity"] == "CRITICAL" for a in active_alerts_list):
            overall = "CRITICAL"
        elif any(a["severity"] == "WARNING" for a in active_alerts_list):
            overall = "WARNING"
        else:
            overall = "NORMAL"

        return {
            "machine_id": machine_id,
            "safety_state": overall,
            "seatbelt_status": "FASTENED",
            "proximity_distance_m": 42.0,
            "active_alerts": active_alerts_list,
            "is_critical": is_critical,
            "critical_alert": critical_alert_dict,
        }


# Global singleton instance
edge_safety_engine = EdgeSafetyEngine()
