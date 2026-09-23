#!/usr/bin/env python3
"""
ShiftGuard -- Data Loader & Validation Suite (Phase 1)
====================================================

Reusable utilities for loading and validating synthetic ShiftGuard datasets.
Enforces physical realism, schema adherence, timestamp monotonicity,
and logical consistency.

Usage:
    python scripts/load_data.py [--data-dir data/synthetic]
"""

import argparse
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Required column specifications
TELEMETRY_COLUMNS = [
    "timestamp",
    "machine_id",
    "operator_id",
    "engine_hours",
    "engine_rpm",
    "engine_load_pct",
    "machine_speed_kmh",
    "fuel_used_l",
    "idling_time_min",
    "load_cycles",
    "operating_state",
    "seatbelt_status",
    "proximity_distance_m",
    "gps_zone",
    "working_condition",
    "coolant_temp_c",
    "hydraulic_oil_temp_c",
    "fault_code",
    "task_id",
]

TASK_COLUMNS = [
    "task_id",
    "machine_id",
    "operator_id",
    "task_type",
    "weather",
    "operator_skill",
    "machine_age_years",
    "estimated_time_min",
    "actual_time_min",
    "planned_start",
    "actual_start",
    "working_condition",
]


def load_csv(filepath: str | Path) -> list[dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path.resolve()}")
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_telemetry_history(filepath: str | Path | None = None) -> list[dict[str, str]]:
    """Load synthetic telemetry history."""
    target = filepath or Path("data/synthetic/telemetry_history.csv")
    return load_csv(target)


def load_task_history(filepath: str | Path | None = None) -> list[dict[str, str]]:
    """Load synthetic task history."""
    target = filepath or Path("data/synthetic/task_history.csv")
    return load_csv(target)


def load_demo_telemetry(filepath: str | Path | None = None) -> list[dict[str, str]]:
    """Load deterministic demo telemetry sequences."""
    target = filepath or Path("data/synthetic/demo_telemetry.csv")
    return load_csv(target)


class DatasetValidator:
    """Rigorous validation suite for ShiftGuard synthetic datasets."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.check_count: int = 0

    def record_check(self):
        self.check_count += 1

    def validate_task_dataset(self, rows: list[dict[str, str]], filename: str = "task_history.csv") -> bool:
        """Validate task history records."""
        initial_errors = len(self.errors)
        
        if not rows:
            self.errors.append(f"[{filename}] Empty dataset.")
            return False

        # 1. Required columns
        self.record_check()
        actual_cols = list(rows[0].keys())
        missing_cols = [c for c in TASK_COLUMNS if c not in actual_cols]
        if missing_cols:
            self.errors.append(f"[{filename}] Missing columns: {missing_cols}")

        task_ids_seen = set()

        for idx, row in enumerate(rows):
            line_no = idx + 2  # 1-based, account for header
            
            # 2. Check task_id uniqueness
            self.record_check()
            t_id = row.get("task_id", "")
            if not t_id or t_id in task_ids_seen:
                self.errors.append(f"[{filename}:L{line_no}] Duplicate or empty task_id '{t_id}'")
            task_ids_seen.add(t_id)

            # 3. Numeric type & non-negative checks
            for num_field in ["machine_age_years", "estimated_time_min", "actual_time_min"]:
                self.record_check()
                val_str = row.get(num_field, "")
                try:
                    val = float(val_str)
                    if val < 0:
                        self.errors.append(f"[{filename}:L{line_no}] Negative value for {num_field}: {val}")
                except ValueError:
                    self.errors.append(f"[{filename}:L{line_no}] Invalid float for {num_field}: '{val_str}'")

            # 4. Timestamp validity & ordering
            self.record_check()
            p_start_str = row.get("planned_start", "")
            a_start_str = row.get("actual_start", "")
            try:
                p_dt = datetime.fromisoformat(p_start_str.replace("Z", "+00:00"))
                a_dt = datetime.fromisoformat(a_start_str.replace("Z", "+00:00"))
                if a_dt < p_dt - timedelta(minutes=15):
                    self.warnings.append(f"[{filename}:L{line_no}] actual_start prematurely before planned_start by >15m")
            except ValueError as e:
                self.errors.append(f"[{filename}:L{line_no}] Invalid ISO8601 timestamp: {e}")

            # 5. Operator skill and weather enum validity
            self.record_check()
            if row.get("operator_skill") not in ["NOVICE", "INTERMEDIATE", "EXPERT"]:
                self.errors.append(f"[{filename}:L{line_no}] Invalid operator_skill: {row.get('operator_skill')}")

        return len(self.errors) == initial_errors

    def validate_telemetry_dataset(self, rows: list[dict[str, str]], filename: str = "telemetry.csv", is_demo: bool = False) -> bool:
        """Validate telemetry time-series dataset."""
        initial_errors = len(self.errors)

        if not rows:
            self.errors.append(f"[{filename}] Empty dataset.")
            return False

        # 1. Required columns
        self.record_check()
        actual_cols = list(rows[0].keys())
        missing_cols = [c for c in TELEMETRY_COLUMNS if c not in actual_cols]
        if missing_cols:
            self.errors.append(f"[{filename}] Missing columns: {missing_cols}")

        # Track monotonicity per machine
        machine_trackers: dict[str, dict[str, Any]] = {}

        for idx, row in enumerate(rows):
            line_no = idx + 2
            m_id = row.get("machine_id", "")
            op_id = row.get("operator_id", "")
            ts_str = row.get("timestamp", "")
            state = row.get("operating_state", "")

            # 2. Machine & Operator ID format
            self.record_check()
            if not m_id or not m_id.startswith("CAT-"):
                self.errors.append(f"[{filename}:L{line_no}] Invalid machine_id format: '{m_id}'")
            if not op_id or not op_id.startswith("OP-"):
                self.errors.append(f"[{filename}:L{line_no}] Invalid operator_id format: '{op_id}'")

            # 3. Timestamp parsing
            self.record_check()
            try:
                curr_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except ValueError:
                self.errors.append(f"[{filename}:L{line_no}] Invalid timestamp: '{ts_str}'")
                curr_dt = None

            # 4. Numeric fields type & range checks
            num_fields = {
                "engine_hours": (0.0, 100000.0),
                "engine_rpm": (0.0, 3500.0),
                "engine_load_pct": (0.0, 100.0),
                "machine_speed_kmh": (0.0, 120.0),
                "fuel_used_l": (0.0, 10000.0),
                "idling_time_min": (0.0, 1440.0),
                "load_cycles": (0, 10000),
                "proximity_distance_m": (0.0, 500.0),
                "coolant_temp_c": (10.0, 130.0),
                "hydraulic_oil_temp_c": (10.0, 125.0),
            }

            parsed_vals = {}
            for field, (min_v, max_v) in num_fields.items():
                self.record_check()
                raw_v = row.get(field, "")
                try:
                    val = float(raw_v)
                    parsed_vals[field] = val
                    if val < min_v or val > max_v:
                        self.errors.append(f"[{filename}:L{line_no}] {field} out of physical range [{min_v}, {max_v}]: {val}")
                except ValueError:
                    self.errors.append(f"[{filename}:L{line_no}] Invalid numeric value for {field}: '{raw_v}'")

            # 5. Seatbelt status check
            self.record_check()
            sblt = row.get("seatbelt_status", "")
            if sblt not in ["FASTENED", "UNFASTENED"]:
                self.errors.append(f"[{filename}:L{line_no}] Invalid seatbelt_status: '{sblt}'")

            # 6. Physical & State Contradiction Checks
            rpm = parsed_vals.get("engine_rpm", 0.0)
            load = parsed_vals.get("engine_load_pct", 0.0)
            speed = parsed_vals.get("machine_speed_kmh", 0.0)

            # Contradiction: Stopped machine moving or high rpm
            self.record_check()
            if state == "STOPPED":
                if speed > 0.1:
                    self.errors.append(f"[{filename}:L{line_no}] Contradiction: STOPPED machine has speed {speed} km/h")
                if rpm > 10.0:
                    self.errors.append(f"[{filename}:L{line_no}] Contradiction: STOPPED machine has RPM {rpm}")

            # Contradiction: IDLE state with excessive speed or high load
            self.record_check()
            if state == "IDLE":
                if speed > 0.1:
                    self.errors.append(f"[{filename}:L{line_no}] Contradiction: IDLE machine has speed {speed} km/h")
                if load > 25.0:
                    self.errors.append(f"[{filename}:L{line_no}] Contradiction: IDLE machine has high load {load}%")

            # Contradiction: Zero RPM but high load
            self.record_check()
            if rpm == 0.0 and load > 0.0:
                self.errors.append(f"[{filename}:L{line_no}] Contradiction: Zero RPM with load {load}%")

            # 7. Monotonicity checks per machine (for continuous time series)
            if not is_demo and curr_dt and m_id:
                self.record_check()
                if m_id not in machine_trackers:
                    machine_trackers[m_id] = {
                        "last_dt": curr_dt,
                        "last_hours": parsed_vals.get("engine_hours", 0.0),
                        "last_fuel": parsed_vals.get("fuel_used_l", 0.0),
                        "last_cycles": parsed_vals.get("load_cycles", 0),
                    }
                else:
                    tracker = machine_trackers[m_id]
                    # Check timestamp strictly increasing or non-decreasing
                    if curr_dt < tracker["last_dt"]:
                        self.errors.append(f"[{filename}:L{line_no}] Timestamp inversion for {m_id}: {curr_dt} < {tracker['last_dt']}")
                    tracker["last_dt"] = curr_dt

                    # Engine hours non-decreasing
                    curr_hours = parsed_vals.get("engine_hours", 0.0)
                    if curr_hours < tracker["last_hours"] - 1e-4:
                        self.errors.append(f"[{filename}:L{line_no}] Engine hours decreased for {m_id}: {curr_hours} < {tracker['last_hours']}")
                    tracker["last_hours"] = curr_hours

                    # Fuel used non-decreasing
                    curr_fuel = parsed_vals.get("fuel_used_l", 0.0)
                    if curr_fuel < tracker["last_fuel"] - 1e-4:
                        self.errors.append(f"[{filename}:L{line_no}] Fuel used decreased for {m_id}: {curr_fuel} < {tracker['last_fuel']}")
                    tracker["last_fuel"] = curr_fuel

                    # Load cycles non-decreasing
                    curr_cycles = parsed_vals.get("load_cycles", 0)
                    if curr_cycles < tracker["last_cycles"]:
                        self.errors.append(f"[{filename}:L{line_no}] Load cycles decreased for {m_id}: {curr_cycles} < {tracker['last_cycles']}")
                    tracker["last_cycles"] = curr_cycles

        return len(self.errors) == initial_errors


def validate_all(synthetic_dir: Path | None = None) -> dict[str, Any]:
    """Validate all generated synthetic datasets in directory."""
    target_dir = synthetic_dir or Path("data/synthetic")
    validator = DatasetValidator()
    
    results = {}

    print("-" * 65)
    print("ShiftGuard Dataset Validation Suite")
    print(f"Target Directory: {target_dir.resolve()}")
    print("-" * 65)

    # 1. Validate task_history.csv
    task_path = target_dir / "task_history.csv"
    if task_path.exists():
        task_rows = load_csv(task_path)
        valid = validator.validate_task_dataset(task_rows, filename="task_history.csv")
        results["task_history"] = {
            "path": str(task_path),
            "rows": len(task_rows),
            "cols": len(task_rows[0]) if task_rows else 0,
            "valid": valid,
        }
        print(f"[OK] task_history.csv: {len(task_rows)} rows, {results['task_history']['cols']} columns -> {'PASS' if valid else 'FAIL'}")
    else:
        validator.errors.append(f"Missing file: {task_path}")
        results["task_history"] = {"valid": False, "error": "File not found"}

    # 2. Validate telemetry_history.csv
    telem_path = target_dir / "telemetry_history.csv"
    if telem_path.exists():
        telem_rows = load_csv(telem_path)
        valid = validator.validate_telemetry_dataset(telem_rows, filename="telemetry_history.csv", is_demo=False)
        results["telemetry_history"] = {
            "path": str(telem_path),
            "rows": len(telem_rows),
            "cols": len(telem_rows[0]) if telem_rows else 0,
            "valid": valid,
        }
        print(f"[OK] telemetry_history.csv: {len(telem_rows)} rows, {results['telemetry_history']['cols']} columns -> {'PASS' if valid else 'FAIL'}")
    else:
        validator.errors.append(f"Missing file: {telem_path}")
        results["telemetry_history"] = {"valid": False, "error": "File not found"}

    # 3. Validate demo_telemetry.csv
    demo_path = target_dir / "demo_telemetry.csv"
    if demo_path.exists():
        demo_rows = load_csv(demo_path)
        valid = validator.validate_telemetry_dataset(demo_rows, filename="demo_telemetry.csv", is_demo=True)
        results["demo_telemetry"] = {
            "path": str(demo_path),
            "rows": len(demo_rows),
            "cols": len(demo_rows[0]) if demo_rows else 0,
            "valid": valid,
        }
        print(f"[OK] demo_telemetry.csv: {len(demo_rows)} rows, {results['demo_telemetry']['cols']} columns -> {'PASS' if valid else 'FAIL'}")
    else:
        validator.errors.append(f"Missing file: {demo_path}")
        results["demo_telemetry"] = {"valid": False, "error": "File not found"}

    total_errors = len(validator.errors)
    total_warnings = len(validator.warnings)
    print("-" * 65)
    print(f"Total Checks Executed: {validator.check_count}")
    print(f"Validation Status: {'PASSED' if total_errors == 0 else 'FAILED'}")
    print(f"Errors: {total_errors} | Warnings: {total_warnings}")
    
    if validator.errors:
        print("\nValidation Errors encountered:")
        for err in validator.errors[:10]:
            print(f"  - {err}")
        if len(validator.errors) > 10:
            print(f"  ... and {len(validator.errors) - 10} more errors.")

    results["passed"] = (total_errors == 0)
    results["error_count"] = total_errors
    results["check_count"] = validator.check_count
    return results


def main():
    parser = argparse.ArgumentParser(description="ShiftGuard Synthetic Dataset Validator")
    parser.add_argument("--data-dir", type=str, default="data/synthetic", help="Path to synthetic datasets")
    args = parser.parse_args()

    results = validate_all(Path(args.data_dir))
    if not results.get("passed", False):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
