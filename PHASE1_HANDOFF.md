# ShiftGuard — Phase 1 Handoff Documentation

> **CRITICAL DIRECTIVE FOR FUTURE AGENTS & TEAMMATES:**  
> **DO NOT CHANGE THESE CONTRACTS WITHOUT A VERY GOOD REASON.**  
> Downstream components (Edge Engine, Anomaly ML, Simulator, Voice, and RAG) depend on the exact database schemas and REST API response models established in Phase 1. Breaking field names, types, or paths will break teammate modules.

---

## 1. What Is Complete (Phase 1 Deliverables)

1. **Synthetic Dataset Generation Pipeline**:
   - `scripts/generate_synthetic_data.py`: Deterministic seed (`SEED = 42`) generating realistic CAT fleet operations.
   - `scripts/load_data.py`: Reusable loader and 56,119-rule physical validation suite (100% PASS).
   - `data/synthetic/task_history.csv` (150 tasks, 12 columns).
   - `data/synthetic/telemetry_history.csv` (3,200 telemetry logs, 19 columns).
   - `data/synthetic/demo_telemetry.csv` (51 deterministic judging scenario records).
   - `DATA_DICTIONARY.md`: Full column-by-column dictionary with physical units and bounds.
2. **SQLite Database Architecture**:
   - SQLite instance `shiftguard.db` created and indexed.
   - 8 SQLAlchemy models implemented in `backend/app/database/models.py`.
   - `telemetry` (3,200 rows) and `tasks` (150 rows) fully seeded.
   - 6 extension tables (`alerts`, `incidents`, `anomalies`, `eta_predictions`, `training_records`, `sync_outbox`) created with primary keys and constraints.
   - Idempotent database initializer `backend/app/database/init_db.py`.
3. **Backend Service Foundation (FastAPI)**:
   - Clean modular architecture in `backend/app/` with settings, database layer, schemas, and routers.
   - REST API endpoints for `/health`, `/api/telemetry/latest`, `/api/telemetry`, `/api/tasks`, `/api/tasks/{task_id}`, `/api/machines`, `/api/operators`.
   - Comprehensive test suite in `backend/tests/` with **32 tests passing** via `python -m pytest`.
4. **React Operator Console Frontend**:
   - React 19 + Vite 8 + Tailwind CSS v4 in `frontend/`.
   - Industrial dark cockpit aesthetic (near-black `#08090c`, grey glassmorphism, restrained emerald green `#10b981`).
   - Modular components: `MachineHeader`, `CurrentTask`, `MachineMetrics`, `SafetyPanel`, `TaskPanel`, `SystemStatus`, `TelemetryValue`, `OperatorConsole`.
   - Dynamic API integration via `frontend/src/services/api.js` with machine switcher and graceful offline cache fallback.
   - Verified production build (`npm run build`) compiling in 1.3s with 0 errors.

---

## 2. What Is NOT Complete (Intentionally Excluded from Phase 1)

The following components are deliberately **NOT** implemented in Phase 1 to preserve team boundaries:
- ❌ CAN bus telemetry simulator daemon
- ❌ WebSocket real-time telemetry streaming
- ❌ Edge safety decision engine & rule evaluation
- ❌ Alert state machine (acknowledgement logic, active alert state machine)
- ❌ Anomaly detection ML model inference
- ❌ ETA ML training and cycle prediction models
- ❌ Multimodal voice assistant (STT / Whisper / TTS)
- ❌ In-cab LLM assistant & RAG manual vector search
- ❌ Model training pipelines and hyperparameter tracking
- ❌ Offline outbox queue processor & sync dispatcher
- ❌ Dockerfiles & Docker Compose
- ❌ AWS cloud infrastructure / S3 / DynamoDB sync

---

## 3. Database Contracts (SQLite: `shiftguard.db`)

All tables are created and managed by SQLAlchemy Declarative Base.

### 3.1 Fully Implemented Tables
```sql
-- Telemetry Table (19 columns)
CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp VARCHAR(64) NOT NULL,
    machine_id VARCHAR(64) NOT NULL,
    operator_id VARCHAR(64) NOT NULL,
    engine_hours FLOAT NOT NULL,
    engine_rpm FLOAT NOT NULL,
    engine_load_pct FLOAT NOT NULL,
    machine_speed_kmh FLOAT NOT NULL,
    fuel_used_l FLOAT NOT NULL,
    idling_time_min FLOAT NOT NULL,
    load_cycles INTEGER NOT NULL,
    operating_state VARCHAR(64) NOT NULL,
    seatbelt_status VARCHAR(32) NOT NULL,
    proximity_distance_m FLOAT NOT NULL,
    gps_zone VARCHAR(64) NOT NULL,
    working_condition VARCHAR(64) NOT NULL,
    coolant_temp_c FLOAT NOT NULL,
    hydraulic_oil_temp_c FLOAT NOT NULL,
    fault_code VARCHAR(64) NOT NULL DEFAULT 'NONE',
    task_id VARCHAR(64) NOT NULL
);
CREATE INDEX ix_telemetry_machine_timestamp ON telemetry (machine_id, timestamp);
CREATE INDEX ix_telemetry_operator_timestamp ON telemetry (operator_id, timestamp);
CREATE INDEX ix_telemetry_task_id ON telemetry (task_id);

-- Tasks Table (12 columns)
CREATE TABLE tasks (
    task_id VARCHAR(64) PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL,
    operator_id VARCHAR(64) NOT NULL,
    task_type VARCHAR(64) NOT NULL,
    weather VARCHAR(64) NOT NULL,
    operator_skill VARCHAR(64) NOT NULL,
    machine_age_years FLOAT NOT NULL,
    estimated_time_min FLOAT NOT NULL,
    actual_time_min FLOAT NOT NULL,
    planned_start VARCHAR(64) NOT NULL,
    actual_start VARCHAR(64) NOT NULL,
    working_condition VARCHAR(64) NOT NULL
);
CREATE INDEX ix_tasks_machine_operator ON tasks (machine_id, operator_id);
```

### 3.2 Extension Tables (Structurally Defined for Teammate Use)
- **`alerts`**: `id` (PK UUID), `machine_id`, `code`, `category`, `severity`, `title`, `message`, `suggested_action`, `acknowledged`, `acknowledged_at`, `timestamp`.
- **`incidents`**: `id` (PK UUID), `machine_id`, `operator_id`, `incident_type`, `severity`, `description`, `gps_zone`, `timestamp`, `resolution_status`.
- **`anomalies`**: `id` (PK UUID), `machine_id`, `sensor_name`, `anomaly_score`, `detected_value`, `expected_range_min`, `expected_range_max`, `timestamp`, `model_version`.
- **`eta_predictions`**: `id` (PK UUID), `task_id` (FK -> `tasks.task_id`), `machine_id`, `predicted_eta_min`, `confidence_score`, `feature_snapshot`, `prediction_timestamp`.
- **`training_records`**: `id` (PK UUID), `model_name`, `model_type`, `dataset_version`, `metrics_json`, `training_start`, `training_end`, `status`.
- **`sync_outbox`**: `id` (PK UUID), `aggregate_type`, `aggregate_id`, `payload`, `created_at`, `synced`, `synced_at`, `retry_count`.

---

## 4. API Contracts (`/api/v1`)

| HTTP Method | Route | Query Parameters | Response Model | Description |
|---|---|---|---|---|
| `GET` | `/health` | None | `HealthResponse` | Health check (`{"status": "ok", "service": "shiftguard-edge", "database": "connected"}`) |
| `GET` | `/api/telemetry/latest` | `machine_id` (optional) | `TelemetryResponse` or `List[TelemetryResponse]` | Returns single machine or full fleet latest readings |
| `GET` | `/api/telemetry` | `machine_id`, `operator_id`, `task_id`, `start_time`, `end_time`, `limit`, `offset` | `List[TelemetryResponse]` | Time-series query with sorting and pagination |
| `GET` | `/api/tasks` | `machine_id`, `operator_id`, `task_type`, `limit`, `offset` | `List[TaskResponse]` | Work orders and haul assignments |
| `GET` | `/api/tasks/{task_id}` | Path parameter | `TaskResponse` | Single task detail by ID (404 if not found) |
| `GET` | `/api/machines` | None | `List[MachineResponse]` | Machine fleet list with latest state, speed, fuel, and hours |
| `GET` | `/api/operators` | None | `List[OperatorResponse]` | Operator list with skill, current machine, and active task |

---

## 5. Dataset Schemas

- **Primary Source**: `data/synthetic/telemetry_history.csv` (19 columns) and `data/synthetic/task_history.csv` (12 columns).
- **Demo Scripting**: `data/synthetic/demo_telemetry.csv` (51 rows encoding 7 judging scenarios: normal operation, seatbelt violation, proximity warning, proximity critical, excessive idle, repeated safety violations, and delayed task).
- **Data Dictionary**: See [DATA_DICTIONARY.md](file:///c:/Users/reape/OneDrive/Desktop/ShiftGuard/DATA_DICTIONARY.md) for full ranges, physical units, and allowed enums.

---

## 6. Frontend Components (`frontend/src/components/`)

- `MachineHeader`: Header bar with fleet selector, operator badge, live UTC clock, and edge status pill.
- `CurrentTask`: Active operation hero banner with countdown ETA, operating phase, and terrain/weather tags.
- `MachineMetrics`: 8-metric primary telemetry cluster (Speed, RPM, Load %, Fuel, Load Cycles, Idle Time, Coolant Temp, Hydraulic Temp).
- `SafetyPanel`: Seatbelt status interlock card, radar proximity distance meter bar, and diagnostic trouble code strip.
- `TaskPanel`: Planned time vs predicted time comparison and next queued auto-dispatched task.
- `SystemStatus`: Edge hardware bus health indicators and explicit Phase 2 reserved badges.
- `TelemetryValue`: Reusable telemetry metric component with tabular numeric formatting and semantic glow.
- `OperatorConsole`: Root layout orchestrating dynamic API polling, machine switching, and graceful offline fallback.

---

## 7. How Future Phases Should Connect

### Phase 2: Telemetry Simulator + WebSocket
- **Location**: `backend/app/edge/` (create simulator daemon) and add WebSocket endpoint `/ws/telemetry` in `backend/app/api/`.
- **How to Connect**: Consume rows from `data/synthetic/telemetry_history.csv` or `demo_telemetry.csv`. Stream records at 1Hz over the WebSocket. Insert streamed records into the `telemetry` table in `shiftguard.db`.
- **Frontend Hook**: In `frontend/src/services/api.js`, connect a WebSocket listener that pushes incoming packets directly into React state.

### Phase 3: Edge Safety Engine
- **Location**: `backend/app/edge/`
- **How to Connect**: Intercept incoming telemetry rows. Check seatbelt violations (`seatbelt_status == 'UNFASTENED'` while `machine_speed_kmh > 0`) and proximity thresholds (`proximity_distance_m < 5.0`). Insert detected events into the `alerts` and `incidents` tables.

### Phase 4: Advanced Operator Console Integration
- **Location**: `frontend/src/components/`
- **How to Connect**: Connect live audio alerts and visual modal banners when new rows appear in `alerts`. Expand `AlertRail` to allow operators to acknowledge alerts.

### Phase 5: Anomaly ML
- **Location**: `backend/app/ml/`
- **How to Connect**: Query historical sensor columns (`engine_rpm`, `engine_load_pct`, `coolant_temp_c`) from the `telemetry` table. Calculate rolling anomaly scores and write detected anomalies to the `anomalies` table.

### Phase 6: ETA ML
- **Location**: `backend/app/ml/`
- **How to Connect**: Read `tasks` and `telemetry` cycle times. Predict remaining cycle completion time and save predictions to `eta_predictions`.

### Phase 7: Voice (STT/TTS)
- **Location**: `backend/app/copilot/`
- **How to Connect**: Capture cab audio input, process speech-to-text, query machine telemetry via the existing FastAPI endpoints, and return synthesized audio response.

### Phase 8: LLM + RAG
- **Location**: `backend/app/copilot/`
- **How to Connect**: Ingest CAT equipment maintenance manuals into a local vector store. Expose endpoint `/api/copilot/ask` that accepts natural language questions and grounds answers in machinery telemetry.

### Phase 9: Training Pipeline
- **Location**: `backend/app/training/`
- **How to Connect**: Load datasets from `data/synthetic/`, run model training scripts, and write run metadata to `training_records`.

### Phase 10: Offline Sync
- **Location**: `backend/app/cloud/`
- **How to Connect**: Watch the `sync_outbox` table. When network connectivity is detected, dispatch pending rows to cloud endpoints and mark `synced = True`.

### Phase 11: Docker Containerization
- **Location**: Root `Dockerfile` and `docker-compose.yml`.
- **How to Connect**: Package FastAPI backend and compiled Vite frontend into a single multi-stage container.

### Phase 12: AWS Cloud Sync
- **Location**: `backend/app/cloud/`
- **How to Connect**: Push aggregated shift summaries and incident records to AWS S3 / DynamoDB.

### Phase 13: Demo Mode
- **Location**: `scripts/`
- **How to Connect**: Replay `data/synthetic/demo_telemetry.csv` step-by-step through the simulator to trigger the 7 prepared judging scenarios deterministically.

---

## 8. Teammate Ownership Matrix

| Phase | Subsystem | Teammate Owner | Phase 1 Status |
|---|---|---|---|
| **Phase 1** | **Datasets, Backend, SQLite, Contracts, React UI** | **Lead Engineer (Complete)** | **COMPLETE & VALIDATED** |
| Phase 2 | Telemetry Simulator + WebSocket | Teammate A | Ready for implementation |
| Phase 3 | Edge Safety Engine | Teammate B | Ready for implementation |
| Phase 4 | Advanced Operator Console Integration | Teammate A/B | Ready for implementation |
| Phase 5 | Anomaly ML | Teammate C | Ready for implementation |
| Phase 6 | ETA ML | Teammate C | Ready for implementation |
| Phase 7 | In-Cab Voice Engine | Teammate D | Ready for implementation |
| Phase 8 | LLM + RAG Assistant | Teammate D | Ready for implementation |
| Phase 9 | Model Training Pipeline | Teammate C | Ready for implementation |
| Phase 10 | Offline Sync Engine | Teammate E | Ready for implementation |
| Phase 11 | Docker Containerization | Teammate E | Ready for implementation |
| Phase 12 | AWS Cloud Sync | Teammate E | Ready for implementation |
| Phase 13 | Demo Runner | Teammate A/E | Ready for implementation |
