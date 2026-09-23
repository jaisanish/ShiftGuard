"""Point-in-time-safe task and live-context features for ETA prediction."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

import pandas as pd


CATEGORICAL_FEATURES = ["task_type", "weather", "operator_skill", "working_condition"]
NUMERIC_FEATURES = [
    "machine_age_years",
    "estimated_time_min",
    "elapsed_minutes",
    "load_cycles_delta",
    "idle_minutes_delta",
    "fuel_used_delta_l",
    "live_context_available",
]
FEATURE_NAMES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def _live_context(telemetry: pd.DataFrame, cutoff_minutes: float = 15.0) -> dict[str, dict[str, float]]:
    if telemetry.empty:
        return {}
    frame = telemetry.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values(["task_id", "timestamp"])
    result: dict[str, dict[str, float]] = {}
    for task_id, group in frame.groupby("task_id"):
        start = group["timestamp"].iloc[0]
        visible = group[group["timestamp"] <= start + pd.Timedelta(minutes=cutoff_minutes)]
        if len(visible) < 2:
            continue
        duration = (visible["timestamp"].iloc[-1] - start).total_seconds() / 60.0
        result[str(task_id)] = {
            "elapsed_minutes": max(float(duration), 0.0),
            "load_cycles_delta": max(float(visible["load_cycles"].iloc[-1] - visible["load_cycles"].iloc[0]), 0.0),
            "idle_minutes_delta": max(float(visible["idling_time_min"].iloc[-1] - visible["idling_time_min"].iloc[0]), 0.0),
            "fuel_used_delta_l": max(float(visible["fuel_used_l"].iloc[-1] - visible["fuel_used_l"].iloc[0]), 0.0),
            "live_context_available": 1.0,
        }
    return result


def build_training_frame(tasks: pd.DataFrame, telemetry: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.Series]:
    required = set(CATEGORICAL_FEATURES + ["machine_age_years", "estimated_time_min", "actual_time_min"])
    missing = required.difference(tasks.columns)
    if missing:
        raise ValueError(f"Task training data is missing columns: {sorted(missing)}")
    if tasks["actual_time_min"].isna().any():
        raise ValueError("ETA target actual_time_min contains missing values")

    context = _live_context(telemetry if telemetry is not None else pd.DataFrame())
    rows = []
    for task in tasks.to_dict(orient="records"):
        live = context.get(str(task.get("task_id")), {
            "elapsed_minutes": 0.0,
            "load_cycles_delta": 0.0,
            "idle_minutes_delta": 0.0,
            "fuel_used_delta_l": 0.0,
            "live_context_available": 0.0,
        })
        rows.append({**{name: task[name] for name in CATEGORICAL_FEATURES}, **{
            "machine_age_years": float(task["machine_age_years"]),
            "estimated_time_min": float(task["estimated_time_min"]),
        }, **live})
    return pd.DataFrame(rows)[FEATURE_NAMES], tasks["actual_time_min"].astype(float).reset_index(drop=True)


def build_inference_row(task: Mapping[str, Any], telemetry: Iterable[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    for field in CATEGORICAL_FEATURES + ["machine_age_years", "estimated_time_min"]:
        if field not in task:
            raise ValueError(f"ETA task input is missing '{field}'")
    live = {
        "elapsed_minutes": 0.0,
        "load_cycles_delta": 0.0,
        "idle_minutes_delta": 0.0,
        "fuel_used_delta_l": 0.0,
        "live_context_available": 0.0,
    }
    records = list(telemetry or [])
    if len(records) >= 2:
        frame = pd.DataFrame(records)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp")
        if len(frame) >= 2:
            live = {
                "elapsed_minutes": max((frame["timestamp"].iloc[-1] - frame["timestamp"].iloc[0]).total_seconds() / 60.0, 0.0),
                "load_cycles_delta": max(float(frame["load_cycles"].iloc[-1] - frame["load_cycles"].iloc[0]), 0.0),
                "idle_minutes_delta": max(float(frame["idling_time_min"].iloc[-1] - frame["idling_time_min"].iloc[0]), 0.0),
                "fuel_used_delta_l": max(float(frame["fuel_used_l"].iloc[-1] - frame["fuel_used_l"].iloc[0]), 0.0),
                "live_context_available": 1.0,
            }
    return {**{name: str(task[name]) for name in CATEGORICAL_FEATURES}, **{
        "machine_age_years": float(task["machine_age_years"]),
        "estimated_time_min": float(task["estimated_time_min"]),
    }, **live}
