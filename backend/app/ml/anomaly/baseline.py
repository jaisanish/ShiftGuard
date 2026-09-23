"""Operator-specific and global behavioral baselines for anomaly explanations."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.app.ml.anomaly.features import FEATURE_NAMES


def _statistics(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for feature in FEATURE_NAMES:
        series = frame[feature].astype(float)
        result[feature] = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std(ddof=0)),
            "sample_count": int(series.count()),
        }
    return result


def build_baselines(windows: pd.DataFrame, minimum_operator_windows: int = 6) -> dict[str, Any]:
    if windows.empty:
        raise ValueError("Cannot build baselines from an empty feature window set")

    operators: dict[str, Any] = {}
    for operator_id, group in windows.groupby("operator_id"):
        operators[str(operator_id)] = {
            "operator_id": str(operator_id),
            "window_count": int(len(group)),
            "sufficient_history": bool(len(group) >= minimum_operator_windows),
            "statistics": _statistics(group),
        }

    return {
        "minimum_operator_windows": int(minimum_operator_windows),
        "global": {
            "window_count": int(len(windows)),
            "statistics": _statistics(windows),
        },
        "operators": operators,
    }


def select_baseline(baselines: dict[str, Any], operator_id: str) -> dict[str, Any]:
    operator = baselines.get("operators", {}).get(operator_id)
    if operator and operator.get("sufficient_history"):
        return {**operator, "source": "OPERATOR"}
    global_profile = baselines["global"]
    return {
        "operator_id": operator_id,
        "window_count": int(global_profile["window_count"]),
        "sufficient_history": False,
        "statistics": global_profile["statistics"],
        "source": "GLOBAL_FALLBACK",
    }
