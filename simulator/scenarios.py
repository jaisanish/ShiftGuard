"""
ShiftGuard Simulator Scenarios
==============================

Defines 7 deterministic operational scenarios mapped directly to the
validated demo sequences in data/synthetic/demo_telemetry.csv:

1. normal               (TSK-DEMO-01) - Nominal hauling loaded, safe proximity, seatbelt fastened
2. seatbelt_violation   (TSK-DEMO-02) - Vehicle in motion (26 km/h) with unfastened seatbelt
3. proximity_warning    (TSK-DEMO-03) - Spotting near hopper/crusher, distance decreasing 15m -> 8m
4. proximity_critical   (TSK-DEMO-04) - Hazardous proximity (<5m) triggering red alert & auto-stop
5. excessive_idle       (TSK-DEMO-05) - Engine idling continuously exceeding 30-minute threshold
6. repeated_safety      (TSK-DEMO-06) - Compound violations: unfastened belt + critical proximity
7. eta_delay            (TSK-DEMO-07) - Muddy incline, severe traction slip, engine load 95.5%

Ensures 100% deterministic behavior without random runtime jitter.
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("shiftguard.simulator.scenarios")

# Mapping scenario names to demo task identifiers
SCENARIO_TASK_MAP = {
    "normal": "TSK-DEMO-01",
    "seatbelt_violation": "TSK-DEMO-02",
    "proximity_warning": "TSK-DEMO-03",
    "proximity_critical": "TSK-DEMO-04",
    "excessive_idle": "TSK-DEMO-05",
    "repeated_safety": "TSK-DEMO-06",
    "eta_delay": "TSK-DEMO-07",
}

SCENARIO_DESCRIPTIONS = {
    "normal": "Nominal loaded hauling on haul road north with nominal separation (42m) and zero faults.",
    "seatbelt_violation": "Safety violation: Haul truck at 26.0 km/h with unfastened seatbelt (SEC-SBLT-WARN).",
    "proximity_warning": "Amber warning: Spotting at crusher feed with distance closing to 8.2m (PRX-WARN-AMBER).",
    "proximity_critical": "Critical alarm: Dangerously close obstacle (<3m) causing emergency stop (PRX-CRIT-RED).",
    "excessive_idle": "Productivity alert: Wheel loader idling continuously past 30 minutes in staging bay (IDL-EXCESS-WARN).",
    "repeated_safety": "Compound hazard: Dozer unfastened belt in severe terrain with 4.8m proximity (SEC-SAFETY-STANDDOWN).",
    "eta_delay": "Cycle delay: Haul truck on muddy steep ramp, 95.5% engine load, speed 6.8 km/h (TSK-DELAY-TRACTION).",
}

# Fallback dataset search paths
CSV_CANDIDATE_PATHS = [
    Path("data/synthetic/demo_telemetry.csv"),
    Path(__file__).resolve().parent.parent / "data" / "synthetic" / "demo_telemetry.csv",
]


def load_demo_csv() -> List[Dict[str, Any]]:
    """Load raw records from demo_telemetry.csv with numeric conversions."""
    csv_file = None
    for p in CSV_CANDIDATE_PATHS:
        if p.exists():
            csv_file = p
            break

    if not csv_file:
        raise FileNotFoundError(
            f"Cannot find demo_telemetry.csv in expected locations: {[str(p) for p in CSV_CANDIDATE_PATHS]}"
        )

    records = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = {
                "timestamp": row["timestamp"],
                "machine_id": row["machine_id"],
                "operator_id": row["operator_id"],
                "engine_hours": float(row["engine_hours"]),
                "engine_rpm": float(row["engine_rpm"]),
                "engine_load_pct": float(row["engine_load_pct"]),
                "machine_speed_kmh": float(row["machine_speed_kmh"]),
                "fuel_used_l": float(row["fuel_used_l"]),
                "idling_time_min": float(row["idling_time_min"]),
                "load_cycles": int(row["load_cycles"]),
                "operating_state": row["operating_state"],
                "seatbelt_status": row["seatbelt_status"],
                "proximity_distance_m": float(row["proximity_distance_m"]),
                "gps_zone": row["gps_zone"],
                "working_condition": row["working_condition"],
                "coolant_temp_c": float(row["coolant_temp_c"]),
                "hydraulic_oil_temp_c": float(row["hydraulic_oil_temp_c"]),
                "fault_code": row["fault_code"],
                "task_id": row["task_id"],
            }
            records.append(parsed)

    return records


def get_scenario_records(
    scenario_name: str,
    machine_id: Optional[str] = None,
    operator_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve deterministic telemetry records for a named scenario.
    Optionally overrides machine_id and operator_id.
    """
    clean_name = scenario_name.strip().lower()
    if clean_name not in SCENARIO_TASK_MAP:
        valid_scenarios = list(SCENARIO_TASK_MAP.keys())
        raise ValueError(
            f"Unknown scenario '{scenario_name}'. Valid options: {valid_scenarios}"
        )

    target_task_id = SCENARIO_TASK_MAP[clean_name]
    all_records = load_demo_csv()

    scenario_records = [
        dict(r) for r in all_records if r.get("task_id") == target_task_id
    ]

    if not scenario_records:
        raise ValueError(f"No records found for task_id '{target_task_id}' in demo_telemetry.csv")

    # Apply optional overrides
    for rec in scenario_records:
        if machine_id:
            rec["machine_id"] = machine_id
        if operator_id:
            rec["operator_id"] = operator_id

    return scenario_records
