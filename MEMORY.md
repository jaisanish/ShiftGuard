# ShiftGuard — Smart Operator Assistant for CAT Machinery
## Project Memory & Architectural Baseline (Phase 2.0)

---

### 1. Project Purpose
ShiftGuard is an intelligent, ruggedized operator assistant and cab interface designed for Caterpillar (CAT) heavy earthmoving and mining machinery (such as CAT 797F Haul Trucks, CAT 6060 Hydraulic Mining Shovels, CAT 994K Wheel Loaders, and CAT D11 Track Dozers). 

The platform provides real-time in-cab situational awareness, machinery health monitoring, haul cycle productivity tracking, deterministic edge safety enforcement, and voice/RAG operator guidance under harsh mining conditions.

---

### 2. Architecture Philosophy & Core Safety Invariants

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NON-NEGOTIABLE SAFETY INVARIANTS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. The Edge Safety Engine is 100% DETERMINISTIC and LOCAL.                  │
│ 2. Machine Learning is NEVER required for immediate cab safety.             │
│ 3. The LLM must NEVER decide safety, change severity, suppress alerts,      │
│    or override the safety engine.                                           │
│ 4. If network or cloud connectivity drops, in-cab safety and telemetry      │
│    recording operate with ZERO degradation (Local-First Offline Baseline).   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3. Engineering Ownership & Scope Breakdown

#### Full-Stack Lead Engineer (My Ownership):
The Full-Stack Engineer owns the complete production-like prototype application stack:
- **Frontend**: Industrial React 19 cockpit console, telemetry gauges, alert state visualizer, voice UI, task panels.
- **Backend & APIs**: FastAPI REST routes, WebSocket ingestion and streaming endpoints, CORS, lifespan lifecycle.
- **Persistence & Database**: SQLite edge database (`shiftguard.db`), SQLAlchemy ORM models, migration/seed loaders.
- **Deterministic Edge Safety Engine**: Real-time rule evaluation, proximity radar interlocks, seatbelt interlocks, thermal boundaries.
- **Alert State Machine**: Transition logic (`ACTIVE` -> `ACKNOWLEDGED` -> `CLEARED`), escalation timers, audio triggers.
- **Telemetry Simulator**: CAN Bus / J1939 emulation, configurable playback speeds, dynamic hazard injection.
- **WebSocket Infrastructure**: High-frequency duplex streaming between simulator, edge backend, and React cab console.
- **Sync Outbox & Cloud Sync**: Local-first transactional outbox, SQLite -> Cloud PostgreSQL sync, offline-resilient queuing.
- **Copilot & Intent Routing**: Deterministic regex router for telemetry/tasks vs. LLM/RAG routing for diagnostic troubleshooting.
- **LLM & In-Cab RAG Integration**: In-cab manual retrieval, context synthesis, guardrail boundaries.
- **Voice Interface**: Audio capture, STT pipeline integration, TTS audio feedback.
- **Operator Training System**: Shift scorecards, cycle benchmark analysis, coaching recommendations.
- **ML Integration APIs & Contracts**: Stable abstract classes (`AnomalyPredictor`, `ETAPredictor`), Pydantic contract schemas.
- **Containerization & Deployment**: Docker, Docker Compose, AWS cloud synchronization.

#### Teammate Ownership (ML MODEL DEVELOPMENT ONLY):
Other teammates own **ONLY** the data science model training and evaluation:
- Anomaly detection model training (isolation forest, autoencoders, etc.)
- Haul cycle ETA model training (gradient boosting, regressors)
- Hyperparameter tuning, cross-validation, and offline metrics
- Model artifact serialization (`.onnx`, `.pt`, `.pkl`)
*Teammates will provide model/inference implementations matching `backend/app/ml/interfaces.py` that the backend will consume.*

---

### 4. Modular Codebase Architecture (`backend/app/`)

```text
backend/app/
├── api/          # REST route handlers (telemetry, tasks, machines, operators, health)
├── edge/         # Edge safety engine, deterministic rule evaluator, alert state machine
├── cloud/        # Cloud sync endpoints, cloud analytics interfaces, AWS bridges
├── database/     # SQLite connection, SQLAlchemy ORM models, seed loaders
├── schemas/      # Pydantic v2 validation contracts (telemetry, tasks, alerts, ML)
├── services/     # Core domain business logic, incident management, audit logging
├── ml/           # Decoupled ML contracts (AnomalyPredictor, ETAPredictor interfaces)
├── copilot/      # In-cab copilot, STT/TTS voice layer, intent router, RAG retrieval
├── training/     # Operator training system, shift analytics, coaching metrics
├── sync/         # Local-first Sync Outbox engine, network monitor, cloud replication
├── simulator/    # CAN bus / J1939 telemetry simulator daemon, hazard injector
├── config.py     # Application settings and environment configuration
└── main.py       # FastAPI application factory, lifespan startup, route mounting
```

---

### 4. Important Technical Decisions

| Layer | Technology | Decision Rationale |
|---|---|---|
| **Runtime Environment** | Windows (PowerShell), Python 3.12, Node.js v24.19 | Detected active host environment. |
| **Backend Framework** | FastAPI + Uvicorn | High performance, native async, automatic OpenAPI docs, strict Pydantic v2 validation. |
| **Database** | SQLite3 via standard library / lightweight async | Self-contained, zero-dependency server setup, easily seedable for local and edge testing. |
| **Frontend Framework** | React 18+ (Vite) | Lightning-fast build tool, lean dependencies, production-grade HMR. |
| **Styling** | Industrial Vanilla CSS / Custom Properties | Zero CSS runtime overhead, complete control over CAT industrial styling (Safety Yellow, high-contrast dark cockpit UI). No Tailwind unless requested. |
| **API Pattern** | RESTful `/api/v1` | Strict request/response schemas allowing clean decoupled consumption by future ML/Voice agents. |

---

### 5. Synthetic Datasets & Domain Schema

> **DISCLAIMER:**  
> All generated datasets are **100% SYNTHETIC** and generated programmatically for demonstration, testing, and development of the ShiftGuard Operator Assistant. They do **NOT** represent actual Caterpillar Inc. production data, machine telemetry, or operational records.

#### 5.1 Dataset Specifications & Deterministic Seed
- **Deterministic Seed**: `SEED = 42` (ensures exact bitwise reproducibility across runs)
- **Generator Script**: `scripts/generate_synthetic_data.py`
- **Validation Script**: `scripts/load_data.py`
- **Output Directory**: `data/synthetic/`
  1. `telemetry_history.csv` — **3,200 rows**, **19 columns**
  2. `task_history.csv` — **150 rows**, **12 columns**
  3. `demo_telemetry.csv` — **51 rows**, **19 columns**

#### 5.2 Exact Schema: `telemetry_history.csv` & `demo_telemetry.csv` (19 Columns)
1. `timestamp` (String, ISO 8601 UTC)
2. `machine_id` (String: `CAT-797F-101`, `CAT-797F-102`, `CAT-6060-201`, `CAT-994K-301`, `CAT-D11-401`)
3. `operator_id` (String: `OP-101` to `OP-105`)
4. `engine_hours` (Float, monotonic non-decreasing per machine)
5. `engine_rpm` (Float: 0 when stopped, 680-740 idle, 1400-2050 working)
6. `engine_load_pct` (Float: 0% stopped, 10-16% idle, 40-70% hauling, 70-98% severe working)
7. `machine_speed_kmh` (Float: 0 stopped/idle, 0.5-3 spotting/dumping, 16-42 hauling)
8. `fuel_used_l` (Float, monotonic cumulative liters consumed)
9. `idling_time_min` (Float, monotonic cumulative idle minutes in IDLE state)
10. `load_cycles` (Integer, monotonic non-decreasing cycle counter)
11. `operating_state` (Enum: `STOPPED`, `IDLE`, `SPOTTING`, `LOADING`, `HAULING_EMPTY`, `HAULING_LOADED`, `DUMPING`, `EXCAVATING`, `DOZING`)
12. `seatbelt_status` (Enum: `FASTENED`, `UNFASTENED` — 99.8% fastened in baseline)
13. `proximity_distance_m` (Float: safe pit distance 18-55m, spotting 6-12m)
14. `gps_zone` (Enum: `PIT_FLOOR_BENCH_A`, `HAUL_ROAD_NORTH`, `CRUSHER_FEED_1`, `OVERBURDEN_DUMP_WEST`, `RAMP_ACCESS_EAST`, `STAGING_BAY_4`)
15. `working_condition` (Enum: `NORMAL`, `MODERATE`, `SEVERE`, `MUDDY`, `STEEP_INCLINE`)
16. `coolant_temp_c` (Float: realistic thermal curve 82°C - 98°C)
17. `hydraulic_oil_temp_c` (Float: thermal range 64°C - 86°C)
18. `fault_code` (String: `NONE`, `ENG-TEMP-HIGH-01`, `PRX-WARN-CLOSE-02`, etc.)
19. `task_id` (String, foreign key reference to `task_history.csv`)

#### 5.3 Exact Schema: `task_history.csv` (12 Columns)
1. `task_id` (String: `TSK-1001` to `TSK-1150`)
2. `machine_id` (String: `CAT-797F-101`, etc.)
3. `operator_id` (String: `OP-101`, etc.)
4. `task_type` (Enum: `OVERBURDEN_REMOVAL`, `ORE_HAULING`, `BENCH_CLEANUP`, `STOCKPILE_FEEDING`, `RAMP_MAINTENANCE`)
5. `weather` (Enum: `CLEAR`, `DUSTY`, `RAIN`, `MUDDY_GROUND`, `FOG`, `HIGH_WIND`)
6. `operator_skill` (Enum: `NOVICE`, `INTERMEDIATE`, `EXPERT`)
7. `machine_age_years` (Float: 2.1 to 6.5 years)
8. `estimated_time_min` (Float: 40.0 to 110.0 minutes)
9. `actual_time_min` (Float: causal function of base time, skill, weather, terrain, and machine age)
10. `planned_start` (String, ISO 8601 UTC)
11. `actual_start` (String, ISO 8601 UTC with dispatch delay offset)
12. `working_condition` (Enum: `NORMAL`, `MODERATE`, `SEVERE`, `MUDDY`, `STEEP_INCLINE`)

#### 5.4 Internal Relationships & Physics Modeling
- **Stopped / Idle Consistency**: Stopped machines have 0 km/h speed, 0 RPM, and 0 load. Idle machines have 0 km/h speed, 680-740 RPM, and 10-16% baseline load.
- **Travelling Dynamics**: Empty trucks travel faster (24-41.5 km/h) with moderate load (42-62%). Loaded trucks travel slower (16-28.5 km/h) under heavy load (72-92%).
- **Cycle & Task Delays**: Actual task durations model real-world operational friction:
  $$\text{multiplier} = 1.0 + \Delta_{\text{skill}} + \Delta_{\text{weather}} + \Delta_{\text{condition}} + (0.015 \times \text{age}) + \epsilon$$
  Expert operators save ~7% time; novice operators add ~16% time; muddy conditions add ~24% delay.
- **Thermal Inertia**: Coolant and hydraulic oil temperatures gradually approach load-dependent setpoints rather than spiking instantaneously.
- **Demo Scenarios (`demo_telemetry.csv`)**: Deterministically scripted sequences for:
  1. *Normal operation*
  2. *Seatbelt violation*
  3. *Proximity warning*
  4. *Proximity critical / emergency stop*
  5. *Excessive idle accumulation*
  6. *Repeated safety violation behavior*
  7. *Delayed task under extreme mud/slope traction drag*

---

### 6. Backend Database Structure & API Contracts (Phase 1 Implemented)

#### 6.1 SQLite Database Schema (8 Tables)
The SQLite database (`shiftguard.db`) defines 8 tables. `telemetry` and `tasks` are fully implemented and seeded; the other 6 provide structured extension points for future phases:

1. **`telemetry`** (Fully Implemented & Seeded):
   - 19 columns: `id` (PK Auto-inc), `timestamp`, `machine_id`, `operator_id`, `engine_hours`, `engine_rpm`, `engine_load_pct`, `machine_speed_kmh`, `fuel_used_l`, `idling_time_min`, `load_cycles`, `operating_state`, `seatbelt_status`, `proximity_distance_m`, `gps_zone`, `working_condition`, `coolant_temp_c`, `hydraulic_oil_temp_c`, `fault_code`, `task_id`.
   - Indexes: `ix_telemetry_machine_timestamp`, `ix_telemetry_operator_timestamp`, `ix_telemetry_task_id`, `ix_telemetry_timestamp`.
2. **`tasks`** (Fully Implemented & Seeded):
   - 12 columns: `task_id` (PK), `machine_id`, `operator_id`, `task_type`, `weather`, `operator_skill`, `machine_age_years`, `estimated_time_min`, `actual_time_min`, `planned_start`, `actual_start`, `working_condition`.
   - Indexes: `ix_tasks_machine_operator`, `ix_tasks_machine_id`, `ix_tasks_operator_id`.
3. **`alerts`** (Structurally Valid Extension):
   - `id` (PK UUID), `machine_id`, `code`, `category`, `severity`, `title`, `message`, `suggested_action`, `acknowledged`, `acknowledged_at`, `timestamp`.
4. **`incidents`** (Structurally Valid Extension):
   - `id` (PK UUID), `machine_id`, `operator_id`, `incident_type`, `severity`, `description`, `gps_zone`, `timestamp`, `resolution_status`.
5. **`anomalies`** (Structurally Valid Extension):
   - `id` (PK UUID), `machine_id`, `sensor_name`, `anomaly_score`, `detected_value`, `expected_range_min`, `expected_range_max`, `timestamp`, `model_version`.
6. **`eta_predictions`** (Structurally Valid Extension):
   - `id` (PK UUID), `task_id` (FK -> `tasks.task_id`), `machine_id`, `predicted_eta_min`, `confidence_score`, `feature_snapshot`, `prediction_timestamp`.
7. **`training_records`** (Structurally Valid Extension):
   - `id` (PK UUID), `model_name`, `model_type`, `dataset_version`, `metrics_json`, `training_start`, `training_end`, `status`.
8. **`sync_outbox`** (Structurally Valid Extension):
   - `id` (PK UUID), `aggregate_type`, `aggregate_id`, `payload`, `created_at`, `synced`, `synced_at`, `retry_count`.

#### 6.2 Implemented API Contracts

| Method | Endpoint | Query Parameters | Description | Status Code |
|---|---|---|---|---|
| `GET` | `/health` | None | Service & database connectivity check | `200 OK` / `503` |
| `GET` | `/api/telemetry/latest` | `machine_id` (optional) | Most recent telemetry (single machine or all fleet machines) | `200 OK` / `404` |
| `GET` | `/api/telemetry` | `machine_id`, `operator_id`, `task_id`, `start_time`, `end_time`, `limit`, `offset` | Historical telemetry time-series | `200 OK` / `422` |
| `GET` | `/api/tasks` | `machine_id`, `operator_id`, `task_type`, `limit`, `offset` | List dispatched work order tasks | `200 OK` / `422` |
| `GET` | `/api/tasks/{task_id}` | Path: `task_id` | Single task detail by identifier | `200 OK` / `404` |
| `GET` | `/api/machines` | None | Fleet list with latest operational state, speed, fuel, and hours | `200 OK` |
| `GET` | `/api/operators` | None | Operator list with skill, current machine, and latest task | `200 OK` |

#### 6.3 Schema Decisions
- **Decoupling**: Frontend consumers and API callers interact strictly with Pydantic response schemas (`TelemetryResponse`, `TaskResponse`, `MachineResponse`, `OperatorResponse`), never directly with SQLAlchemy ORM models.
- **Dataset Parity**: `TelemetryResponse` matches the 19 columns of `telemetry_history.csv` field-for-field; `TaskResponse` matches the 12 columns of `task_history.csv` field-for-field.
- **Validation**: Strict boundary validation via Pydantic v2; requests with invalid bounds or malformed types trigger standard HTTP 422 JSON responses.

---

### 7. Frontend Design System & Architecture (Phase 1 Implemented)

#### 7.1 Visual System & Design Direction
- **Aesthetic**: Dark, industrial, premium, cinematic, futuristic, minimal graphite/black cockpit.
- **Surface**: Grey glassmorphism (`backdrop-filter: blur(12px)`, `rgba(17, 20, 26, 0.75)`, subtle white hairline borders `border-white/[0.07]`, soft dark drop shadows).
- **Subtle Texture**: Dark graphite base with subtle diagonal metallic highlights and micro-hazard accents.
- **Typography**: 
  - Sans-Serif: `Inter` for clean readability and UI metadata.
  - Display: `Space Grotesk` for sharp industrial headers.
  - Monospace: `JetBrains Mono` for machine values, clock, and tabular telemetry.

#### 7.2 Design Tokens & Semantic Palette
- **Base Canvas**: Near-black `#08090c` with subtle radial emerald mesh.
- **Cockpit Glass Surface**: `rgba(17, 20, 26, 0.75)` with `inset 0 1px 0 rgba(255,255,255,0.04)`.
- **Primary Accent**: Restrained Industrial Green (`#10b981`, `#059669`).
- **Semantic Indicators**:
  - `Safe`: Emerald `#10b981` (Interlock secure, normal temps, separation >15m).
  - `Warning`: Amber `#f59e0b` (Obstacle 5-15m, idle >20m, elevated coolant).
  - `Critical`: Crimson `#ef4444` (Seatbelt unfastened in motion, proximity <5m, emergency stop).
  - `Inactive`: Slate grey `#6b7280` / `#4b5563` (Stopped engine, off bus).

#### 7.3 Component Hierarchy
```text
OperatorConsole (Root container, API polling loop, offline fallback banner)
├── MachineHeader (Brand identity, machine selector, operator badge, live clock, edge status)
├── CurrentTask (Hero mission card, ETA minutes, operational phase, cycle counter, terrain/weather)
├── MachineMetrics (8-metric telemetry grid: Speed, RPM, Load %, Fuel, Cycles, Idle, Coolant, Hydraulic)
│   └── TelemetryValue (Reusable metric widget with tabular digits, unit, and semantic glow)
├── SafetyPanel (Seatbelt interlock state, radar proximity meter bar, diagnostic trouble code strip)
├── TaskPanel (Planned duration, predicted duration, operator skill factor, next queued dispatch)
└── SystemStatus (Hardware bus health & explicit Phase 2 reserved placeholders)
```

#### 7.4 API Integration (`services/api.js`)
- `fetchHealth()`: Checks backend status via `GET /health`.
- `fetchLatestTelemetry(machineId)`: Pulls live sensor readings via `GET /api/telemetry/latest`.
- `fetchTasks(params)`: Queries work orders via `GET /api/tasks`.
- `fetchTaskById(taskId)`: Queries specific assignment via `GET /api/tasks/{task_id}`.
- `fetchMachines()`: Populates machine switcher via `GET /api/machines`.
- **Fault-Tolerant Offline Cache**: If the backend is temporarily offline, the service falls back gracefully to a clean cached state with an in-cab amber notification banner rather than breaking the UI.

#### 7.5 Explicit Future Placeholders (No Phase 1 Business Logic)
- **Safety Engine**: Marked `READY` (reserved for future edge rules engine).
- **Cloud Connection**: Marked `NOT CONNECTED` (reserved for future AWS sync).
- **Sync Outbox**: Marked `0 PENDING` (reserved for local-first event queue).
- **Voice Copilot**: Visual badge `STANDBY (PHASE 2 RESERVED)`.
- **Anomaly ML Engine**: Visual badge `STANDBY (PHASE 2 RESERVED)`.
- **In-Cab RAG Manuals**: Visual badge `STANDBY (PHASE 2 RESERVED)`.

---

### 8. Important Constraints & Invariants (Must NOT Break)
1. **Schema Stability**: Schema field names and types in `telemetry`, `tasks`, and database models must remain stable for downstream consumers.
2. **Database Portability**: Use standard SQLite types so the DB file is portable across edge devices and developer machines.
3. **API Shape**: Backend endpoints must always return structured JSON matching defined Pydantic schemas.
4. **Safety Separation**: ML or LLM must NEVER override the deterministic edge safety engine.

---

### 9. Phase 2.1 Live Telemetry Simulator & Streaming Infrastructure

#### 9.1 Dataflow & Pipeline
```text
data/synthetic/demo_telemetry.csv
               ↓
    Python Replay Simulator (simulator/replay.py)
               ↓
    WebSocket (/ws/telemetry?role=simulator)
               ↓
       FastAPI Edge Ingestion
               ↓
       TelemetryService (Pydantic Schema Validation)
               ↓
       SQLite Database (shiftguard.db Persistence)
               ↓
    TelemetryBroadcastService (Multi-Client Broadcaster)
               ↓
    React In-Cab Operator Console (Sub-100ms Live Telemetry)
```

#### 9.2 Scenarios Implemented (100% Deterministic)
1. `normal` (`TSK-DEMO-01`): Nominal loaded hauling, 32.5 km/h, seatbelt fastened, 42.0m clearance.
2. `seatbelt_violation` (`TSK-DEMO-02`): Unfastened seatbelt while moving at 26.0 km/h (`SEC-SBLT-WARN`).
3. `proximity_warning` (`TSK-DEMO-03`): Spotting near crusher with clearance closing 15.2m → 8.2m (`PRX-WARN-AMBER`).
4. `proximity_critical` (`TSK-DEMO-04`): Rapid clearance reduction <3m triggering emergency auto-stop (`PRX-CRIT-RED`, `PRX-CRIT-STOP`).
5. `excessive_idle` (`TSK-DEMO-05`): Continuous idling in staging bay reaching 35 minutes (`IDL-EXCESS-WARN`).
6. `repeated_safety` (`TSK-DEMO-06`): Multi-violation compound hazard (unfastened + 4.8m proximity) -> stand-down (`SEC-SAFETY-STANDDOWN`).
7. `eta_delay` (`TSK-DEMO-07`): Severe muddy ramp haul, 95.5% engine load, speed dropped to 6.8 km/h (`TSK-DELAY-TRACTION`).

#### 9.3 CLI Usage
- `python simulator/replay.py --scenario normal`
- `python simulator/replay.py --scenario seatbelt_violation --speed 2.0`
- `python simulator/replay.py --scenario proximity_critical --machine-id CAT-797F-101`
- `python simulator/replay.py --scenario normal --loop`

#### 9.4 Logging Standardization
Standardized log prefixes trace the entire event lifecycle:
- `[SIMULATOR]` : Transmissions, connects, reconnects, server acks.
- `[EDGE INGESTION]` : Ingestion frames received from simulator connections.
- `[TELEMETRY VALIDATION]` : Pydantic boundary and schema validation results.
- `[TELEMETRY STORAGE]` : SQLite database persistence and duplicate detection.
- `[WEBSOCKET BROADCAST]` : Fan-out broadcasts to connected frontend cockpits.

---

### 10. Phase 2.x — Operator Console Clean-Up, Semantics & Training Hub

#### 10.1 Operator Identity Convention
- **Rule**: The application must **NEVER** display fabricated human operator names (e.g. "Elena Vance").
- **Display Label**: Strictly displayed as `"OPERATOR 1"`.
- **Internal Identifier**: The backend and synthetic datasets use an anonymized identifier such as `OP-001` or `OP-101`.
- **Privacy & Safety Invariant**: In-cab telemetry, audit trails, and dispatch logs avoid inventing personal human personas.

#### 10.2 Operating State vs Task Phase Distinction
- **Operating State** (`OPERATING STATE`):
  - Represents the **current physical machine kinematic state**.
  - Must take one of four canonical states:
    - `IDLE`: Engine running (RPM > 300), ground speed < 1 km/h.
    - `WORKING`: Active haulage / loading under engine load.
    - `TRAVELLING`: Ground speed >= 1 km/h.
    - `STOPPED`: Engine shutdown (RPM = 0, speed = 0).
  - Value is derived strictly from real-time telemetry events (CAN Bus / simulator) and updates with sub-100ms latency via WebSocket.
- **Task Phase** (`TASK PHASE`):
  - Optional operational dispatch lifecycle concept (e.g. `DIGGING`, `LOADING`, `HAULING`, `DUMPING`, `RETURN`).
  - `IDLE` is an operating state, **never** a task phase.
  - UI strictly displays `OPERATING STATE` on the telemetry hero card.

#### 10.3 Co-Pilot Services (Subsystem Status)
- Internal development-phase terminology ("FUTURE COCKPIT SUBSYSTEMS (PHASE 2 RESERVED)") removed from operator-facing displays.
- Renamed to **"CO-PILOT SERVICES"** with realistic subsystem status indicators:
  - `VOICE COPILOT`: `STANDBY`
  - `ANOMALY ANALYTICS`: `STANDBY`
  - `IN-CAB MANUALS`: `READY`
  - `SAFETY ENGINE`: `READY`
- Legitimate status codes: `READY`, `STANDBY`, `NOT CONFIGURED`, `CONNECTED`, `OFFLINE`.

#### 10.4 Training Hub Foundation & Architecture
- **Top-Level Surface**: Dedicated `COACH` tab in the cockpit navigation bar.
- **Components**:
  - `CoachPage`: Master container orchestrating library, recommendations, active lessons, quizzes, and history.
  - `TrainingRecommendation`: Hero card displaying the recommended lesson, specific trigger reason (e.g., repeated proximity trips), duration, and direct launch CTA.
  - `TrainingLibrary`: Catalog of available safety, efficiency, and compliance modules.
  - `TrainingLesson`: Lesson viewer supporting video playback with automatic fallback notice (`Training media not configured` when physical assets are absent), module overview, and key operational protocols.
  - `TrainingQuiz`: Interactive 3-question compliance assessment calculating real-time percentage scores, pass/fail status, and persistence to backend history.
  - `TrainingHistory`: Tabular log of past completed training sessions, scores, and timestamps.
- **Cockpit Integration**:
  - Compact **`COACHING MOMENT`** card rendered above the telemetry deck in Command Center when an active recommendation exists.
  - Single-click transition from `[ START TRAINING ]` directly into the targeted lesson inside the Coach Hub.
- **Backend & Frontend Contracts**:
  - `TrainingRecommendation`: `id`, `operator_id`, `lesson_id`, `reason`, `urgency`, `recommended_at`, `lesson`.
  - `Lesson`: `lesson_id`, `title`, `category`, `duration_minutes`, `description`, `media_url`, `pdf_url`, `key_points`, `quiz`.
  - `QuizQuestion`: `question_id`, `question`, `options`, `correct_answer_index`, `explanation`.
  - `TrainingCompletionRequest`: `operator_id`, `lesson_id`, `score`, `passed`.
  - `TrainingHistoryItem`: `id`, `operator_id`, `lesson_id`, `lesson_title`, `score`, `passed`, `completed_at`.

---

### 11. Phase 4 — Realtime Operator Console & Edge Safety Engine Integration

#### 11.1 Real-Time Telemetry Streaming Architecture
- **Single Persistent Connection**: Frontend establishes a single bi-directional WebSocket connection to `/ws/telemetry?role=frontend` via `RealtimeContext.jsx`.
- **Initial Snapshot Sync**: Server transmits `telemetry_initial` containing both latest physical telemetry snapshot and authoritative `safety_snapshot` immediately upon connection.
- **Zero Browser Refresh**: All primary metrics (`machine_speed_kmh`, `engine_rpm`, `engine_load_pct`, `fuel_used_l`, `load_cycles`, `idling_time_min`, `operating_state`, `seatbelt_status`, `proximity_distance_m`, `timestamp`) update visibly with zero refresh.
- **Stale Detection**: Tracks `secondsSinceUpdate` every 1000ms. Displays warning if telemetry paused for >8 seconds.

#### 11.2 Invariant Enforcement: Zero Fabricated Predicted ETA
- **Strict Invariant**: The operator console **never** fabricates an estimated time of completion using hardcoded multipliers.
- **Display Status**: `MODEL PENDING` or `ETA MODEL NOT CONNECTED` prominently rendered with explanatory notice that ML model pipelines (Phase 6) are required.

#### 11.3 Authoritative Operating State
- Direct reflection of backend canonicalized state (`IDLE`, `WORKING`, `TRAVELLING`, `STOPPED`).
- Mapping is enforced centrally in `to_canonical_operating_state()` on both WebSocket broadcast and REST endpoints. Frontend never guesses kinematic state.

#### 11.4 Authoritative Edge Safety & Critical Alert Overlay
- `EdgeSafetyEngine` executes deterministic safety rules locally:
  - `SeatbeltSafetyRule`: Detects unfastened seatbelt while machine in motion (speed > 0.5 km/h). Escalates DETECTED -> WARNING (>=3s) -> CRITICAL (>=6s).
  - `ProximitySafetyRule`: Evaluates radar separation (<15m CAUTION, <5m WARNING, <2m CRITICAL with dynamic velocity anticipation).
- **Critical Alert Overlay**: Dominant, high-contrast modal overlay triggered exclusively by backend `CRITICAL` events. Features diagonal warning stripes, prominent metric display, and `[ ACKNOWLEDGE HAZARD ]` action.
- **Audit Logging**: Acknowledging hazards persists operator ID and timestamp to SQLite `alerts` / `incidents` tables and fans out `alert_acknowledged` via WebSocket.

#### 11.5 Incidents System & Rich Physical Context Buffers
- `IncidentContextBuffer` maintains a sliding in-memory circular window of 60s of telemetry frames.
- When an incident is declared, it captures a 30s pre-event window, the trigger frame, and subsequent post-event frames, persisting them as JSON in SQLite `incidents` table.
- Dedicated `IncidentsPage` provides an audit registry and `[ INSPECT ]` modal displaying the full context buffer across pre-event, trigger, and post-event phases.

#### 11.6 Command Center Visuals & Mini Rolling Sparklines
- Premium dark industrial theme (`#08090c`, graphite `#12151d`, muted emerald/amber/rose).
- Compact rolling SVG sparklines (`Sparkline.jsx`) rendering the last 30–50 samples for Speed, RPM, Engine Load %, and Proximity Clearance.
- Horizontal utilization bar for Engine Load %.
- Compact `ASK SHIFTGUARD` voice/text in-cab query entry (`CopilotEntry.jsx`).
- System integrity indicators: `EDGE COMPUTE: ACTIVE`, `SAFETY ENGINE: LOCAL`, `WEBSOCKET: CONNECTED`, `CLOUD: DISCONNECTED`, `SYNC: 0 PENDING`.

