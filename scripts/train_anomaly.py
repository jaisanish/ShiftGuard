"""Train the Phase 6 anomaly model outside FastAPI startup."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ml.anomaly.train import DEFAULT_MODEL_VERSION, train_anomaly_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ShiftGuard Isolation Forest anomaly model")
    parser.add_argument("--telemetry", type=Path, default=Path("data/synthetic/telemetry_history.csv"))
    parser.add_argument("--demo", type=Path, default=Path("data/synthetic/demo_telemetry.csv"))
    parser.add_argument(
        "--artifact",
        type=Path,
        default=Path("backend/app/ml/anomaly/artifacts/shiftguard_anomaly_v1.joblib"),
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("backend/app/ml/anomaly/artifacts/shiftguard_anomaly_v1.metadata.json"),
    )
    parser.add_argument("--model-version", default=DEFAULT_MODEL_VERSION)
    args = parser.parse_args()

    metadata = train_anomaly_model(
        telemetry_csv=args.telemetry,
        demo_csv=args.demo,
        artifact_path=args.artifact,
        metadata_path=args.metadata,
        model_version=args.model_version,
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
