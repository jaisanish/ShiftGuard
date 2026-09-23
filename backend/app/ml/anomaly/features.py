"""Causal rolling-window feature engineering for ShiftGuard anomaly analytics."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


WINDOW_MINUTES = 15
MIN_WINDOW_SAMPLES = 4

FEATURE_NAMES = [
    "idle_ratio",
    "fuel_per_load_cycle",
    "load_cycles_per_hour",
    "fuel_per_active_hour",
    "safety_alert_rate",
    "seatbelt_violation_rate",
]

REQUIRED_COLUMNS = {
    "timestamp",
    "machine_id",
    "operator_id",
    "fuel_used_l",
    "idling_time_min",
    "load_cycles",
    "operating_state",
    "seatbelt_status",
    "machine_speed_kmh",
    "proximity_distance_m",
    "fault_code",
}


def _as_dataframe(records: pd.DataFrame | Iterable[Mapping[str, Any]]) -> pd.DataFrame:
    frame = records.copy() if isinstance(records, pd.DataFrame) else pd.DataFrame(list(records))
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Telemetry feature input is missing columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Telemetry feature input is empty")

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if frame["timestamp"].isna().any():
        raise ValueError("Telemetry contains invalid timestamps")

    numeric_columns = [
        "fuel_used_l",
        "idling_time_min",
        "load_cycles",
        "machine_speed_kmh",
        "proximity_distance_m",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[numeric_columns].isna().any().any():
        raise ValueError("Telemetry contains missing or non-numeric feature inputs")
    return frame.sort_values(["machine_id", "operator_id", "timestamp"]).reset_index(drop=True)


def _observed_hours(group: pd.DataFrame) -> float:
    """Return causal observed duration, including one representative sample interval."""
    timestamps = group["timestamp"].sort_values()
    if len(timestamps) == 1:
        return 0.0
    deltas = timestamps.diff().dropna().dt.total_seconds()
    positive = deltas[deltas > 0]
    sample_seconds = float(positive.median()) if not positive.empty else 0.0
    span_seconds = float((timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds())
    return max((span_seconds + sample_seconds) / 3600.0, 0.0)


def build_feature_window(records: pd.DataFrame | Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build one leakage-free feature vector from records available inside a window."""
    group = _as_dataframe(records)
    if len(group) < 2:
        raise ValueError("At least two telemetry samples are required for a feature window")
    if group[["machine_id", "operator_id"]].drop_duplicates().shape[0] != 1:
        raise ValueError("A feature window must contain one machine/operator pair")

    duration_hours = _observed_hours(group)
    if duration_hours <= 0:
        raise ValueError("Feature window duration must be positive")

    states = group["operating_state"].astype(str).str.upper()
    speeds = group["machine_speed_kmh"].astype(float)
    belts = group["seatbelt_status"].astype(str).str.upper()
    fault_codes = group["fault_code"].fillna("NONE").astype(str).str.upper()

    idle_mask = states.eq("IDLE")
    active_mask = ~states.isin(["IDLE", "STOPPED"])
    seatbelt_violation = belts.eq("UNFASTENED") & speeds.gt(0.5)
    safety_sample = (
        seatbelt_violation
        | group["proximity_distance_m"].astype(float).lt(15.0)
        | fault_codes.str.startswith(("SEC-", "PRX-"))
    )

    fuel_delta = max(float(group["fuel_used_l"].iloc[-1] - group["fuel_used_l"].iloc[0]), 0.0)
    cycle_delta = max(float(group["load_cycles"].iloc[-1] - group["load_cycles"].iloc[0]), 0.0)
    active_hours = duration_hours * float(active_mask.mean())

    features = {
        "idle_ratio": float(idle_mask.mean()),
        "fuel_per_load_cycle": float(fuel_delta / max(cycle_delta, 1.0)),
        "load_cycles_per_hour": float(cycle_delta / duration_hours),
        "fuel_per_active_hour": float(fuel_delta / active_hours) if active_hours > 0 else 0.0,
        "safety_alert_rate": float(safety_sample.mean()),
        "seatbelt_violation_rate": float(seatbelt_violation.mean()),
    }

    if not all(np.isfinite(value) for value in features.values()):
        raise ValueError("Feature engineering produced a non-finite value")

    return {
        "machine_id": str(group["machine_id"].iloc[0]),
        "operator_id": str(group["operator_id"].iloc[0]),
        "window_start": group["timestamp"].iloc[0].isoformat().replace("+00:00", "Z"),
        "window_end": group["timestamp"].iloc[-1].isoformat().replace("+00:00", "Z"),
        "sample_count": int(len(group)),
        **features,
    }


def build_feature_windows(
    records: pd.DataFrame | Iterable[Mapping[str, Any]],
    window_minutes: int = WINDOW_MINUTES,
    min_samples: int = MIN_WINDOW_SAMPLES,
) -> pd.DataFrame:
    """Build fixed, past-only windows independently for each machine/operator pair."""
    frame = _as_dataframe(records)
    frame["window_bucket"] = frame["timestamp"].dt.floor(f"{window_minutes}min")

    windows: list[dict[str, Any]] = []
    group_columns = ["machine_id", "operator_id", "window_bucket"]
    for _, group in frame.groupby(group_columns, sort=True):
        if len(group) < min_samples:
            continue
        windows.append(build_feature_window(group.drop(columns=["window_bucket"])))

    if not windows:
        return pd.DataFrame(columns=[
            "machine_id", "operator_id", "window_start", "window_end", "sample_count", *FEATURE_NAMES
        ])
    return pd.DataFrame(windows).sort_values(["window_start", "machine_id"]).reset_index(drop=True)


def feature_matrix(windows: pd.DataFrame) -> np.ndarray:
    """Return the stable model matrix in the versioned feature order."""
    missing = set(FEATURE_NAMES).difference(windows.columns)
    if missing:
        raise ValueError(f"Feature window is missing model fields: {sorted(missing)}")
    matrix = windows[FEATURE_NAMES].astype(float).to_numpy()
    if not np.isfinite(matrix).all():
        raise ValueError("Feature matrix contains NaN or infinite values")
    return matrix
