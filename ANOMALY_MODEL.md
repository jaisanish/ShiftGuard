# Phase 6 — Anomaly Analytics

ShiftGuard Phase 6 detects unusual operating patterns using a versioned Isolation Forest. It is an advisory analytics subsystem. It cannot create, suppress, acknowledge, or change a safety alert; deterministic edge rules remain the only immediate safety authority.

## Pipeline

```text
historical telemetry
  → causal 15-minute windows
  → robust scaling
  → Isolation Forest
  → calibrated anomaly score
  → operator/global baseline evidence
  → SQLite anomaly record
  → sync outbox
  → cloud anomaly history
  → REST API + React Insights UI
```

## Training

Run training explicitly; FastAPI never trains during startup:

```bash
python scripts/train_anomaly.py
```

The command validates the source schema and writes:

- `backend/app/ml/anomaly/artifacts/shiftguard_anomaly_v1.joblib`
- `backend/app/ml/anomaly/artifacts/shiftguard_anomaly_v1.metadata.json`

The metadata records the model version, feature schema, dataset SHA-256, training timestamp, hyperparameters, score calibration, operator baselines, and controlled-scenario diagnostics. The application only loads its configured trusted local artifact. Joblib files from untrusted sources must never be loaded.

## Baselines and evidence

An operator receives an operator-specific baseline after at least six historical windows. Otherwise inference uses the global fleet baseline and labels the source `GLOBAL_FALLBACK`. Explanations compare each current feature with the selected baseline median and standard deviation. Human-readable types are post-processing labels over model evidence:

- `EXCESSIVE_IDLE`
- `HIGH_FUEL_USAGE`
- `LOW_PRODUCTIVITY`
- `REPEATED_SAFETY_PATTERN`
- `UNUSUAL_OPERATION`

The Isolation Forest itself does not understand these semantic concepts.

## APIs

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/anomalies/model/health` | Artifact version, training time, dataset and readiness |
| `GET` | `/api/anomalies/latest-inference` | Read-only inference on the latest complete feature window |
| `POST` | `/api/anomalies/analyze` | Infer and persist an unusual result idempotently |
| `GET` | `/api/anomalies` | Filtered persisted anomaly history |
| `GET` | `/api/anomalies/{id}` | One persisted result |
| `GET` | `/api/operators/{operator_id}/baseline` | Operator profile or global fallback |
| `GET` | `/api/operators/{operator_id}/anomaly-summary` | Counts, latest result and model health |
| `GET` | `/api/cloud/anomalies` | Synchronized cloud anomaly history |

If the artifact is missing, corrupt, or schema-incompatible, model health returns `unavailable`, inference returns HTTP 503, the UI shows `ANALYTICS UNAVAILABLE`, and edge safety continues normally.

## Current synthetic diagnostics

The committed v1 artifact trained on 3,200 synthetic telemetry rows and 160 feature windows. Controlled demo evaluation produced 0.857 accuracy, 1.000 precision and 0.833 recall across seven synthetic scenarios. Six scenarios matched their synthetic expectation. The amber proximity-warning scenario did not cross the model threshold; deterministic proximity safety still handles it correctly.

These are synthetic evaluation labels only. They do not establish real-world accuracy, operator fitness, safety certification, or generalization to Caterpillar equipment.
