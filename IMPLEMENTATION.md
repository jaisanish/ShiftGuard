# ShiftGuard — Implementation Tracker

## 1. Project Status
**Current State**: Phase 4 Realtime Operator Console & Edge Safety Engine Integration Completed & Verified  
**Execution Phase**: Phase 4 Complete (Phase 1, 2.0, 2.1, 3 Intact)  
**Deliverables Status**:
- [x] Phase 1 Core Deliverables (Synthetic Data, SQLite, FastAPI, API Contracts, React Console, Integration)
- [x] Phase 2.0 Architecture Baseline (`ARCHITECTURE.md`, ML contracts, decoupled interfaces, module structure)
- [x] Phase 2.1 Telemetry Simulator & WebSocket Streaming (Completed & Verified)
- [x] Phase 2.x Operator Console Clean-Up, Semantics & Training Hub (Completed & Verified)
- [x] Phase 3 Deterministic Edge Safety Engine & Alert State Machine (Completed & Verified)
- [x] Phase 4 Realtime Operator Console & Incident Context Buffers (Completed & Verified)
- [ ] Phase 5 In-Cab Voice & Copilot (Intent Router, Manual RAG, LLM Integration)
- [ ] Phase 6 ML Model Pipeline Ingestion (Teammate models via `AnomalyPredictor` and `ETAPredictor`)
- [ ] Phase 7 Local-First Sync Outbox & Cloud Sync
- [ ] Phase 8 Docker & Cloud Deployment

---

## 2. Completed Work

### Phase 4 Realtime Operator Console & Edge Safety Engine Integration
- [x] **Live Telemetry WebSocket Stream (Zero Refresh)**:
  - Unified single persistent connection `/ws/telemetry?role=frontend` in `RealtimeContext.jsx`.
  - Immediate `telemetry_initial` sync frame containing latest physical telemetry snapshot and safety status.
  - Sub-100ms streaming updates for RPM, Load %, Speed, Fuel, Cycles, Idle, State, Seatbelt, Proximity, Condition, Timestamp.
  - Active stale detection tracking seconds since update, warning operator when simulator stream is paused (>8s).
- [x] **Strict Zero-Fabricated ETA Invariant**:
  - Removed all hardcoded mathematical formulas (`estimatedMin * 0.72`) calculating fake minutes remaining.
  - Replaced with authoritative status: `MODEL PENDING` / `ETA MODEL NOT CONNECTED` across `CurrentTask` and `TaskPanel`.
  - Explicit explanation to operator: *"Predicted completion times require the ML model pipeline (Phase 6)."*
- [x] **Authoritative Machine Operating State**:
  - Direct reflection of `telemetry.operating_state` from backend single source of truth.
  - Canonicalized via `to_canonical_operating_state()` to `IDLE`, `WORKING`, `TRAVELLING`, `STOPPED`. Zero frontend guessing.
- [x] **Authoritative Edge Safety & Critical Alert Overlay**:
  - Evaluated on backend via `EdgeSafetyEngine` orchestrating `SeatbeltSafetyRule` and `ProximitySafetyRule`.
  - Dominant modal `CriticalAlertOverlay.jsx` triggers exclusively on `CRITICAL` events with diagonal hazard stripes, prominent metric display, and `[ ACKNOWLEDGE HAZARD ]`.
  - Hazard acknowledgment writes operator audit logs to SQLite and broadcasts `alert_acknowledged` over WebSocket.
- [x] **Incidents Registry & Rich Physical Context Buffers**:
  - `IncidentContextBuffer` sliding circular memory window captures 30s pre-event telemetry, trigger frame, and post-event telemetry.
  - Realtime `IncidentNotificationToast.jsx` slides in on `incident_created`.
  - Dedicated `IncidentsPage.jsx` with tabular audit registry and inspection modal viewing pre-event, trigger, and post-event physics.
- [x] **Dedicated Safety Page**:
  - Prominent badge: `SOURCE: LOCAL EDGE SAFETY ENGINE DETERMINISTIC`.
  - Cards for Overall Safety, Seatbelt Interlock, Live Proximity Radar, Operating State.
  - Real-time active alerts and historical logs with acknowledgment controls.
- [x] **Industrial Command Center Aesthetics & Trend Sparklines**:
  - Deep industrial dark theme (`#08090c`, graphite `#12151d`, muted emerald/amber/rose).
  - Compact SVG sparklines (`Sparkline.jsx`) rendering rolling 30–50 samples for Speed, RPM, Load %, and Proximity Clearance.
  - Horizontal utilization bar for Engine Load %.
  - Compact `ASK SHIFTGUARD` voice/text entry (`CopilotEntry.jsx`).
  - Subsystem indicators: `EDGE COMPUTE: ACTIVE`, `SAFETY ENGINE: LOCAL`, `WEBSOCKET: CONNECTED`, `CLOUD: DISCONNECTED`, `SYNC: 0 PENDING`.
- [x] **Automated Testing & Build Verification**:
  - 53 backend automated tests passing cleanly in ~3s (`test_safety.py`, `test_telemetry_ws.py`, `test_telemetry.py`, `test_tasks.py`, `test_health.py`, `test_database.py`, `test_schemas.py`, `test_training.py`).
  - Frontend production build (`npm run build`) compiles cleanly in 1.55s with 0 errors.

### Phase 2.x Clean Operator Console, Semantics & Training Hub Foundation
- [x] **Operator Identity Elimination**:
  - Removed all fabricated human operator names (e.g. "Elena Vance") from synthetic data generators, database models, frontend components, and tests.
  - Standardized operator display identity strictly to `"OPERATOR 1"` with backend anonymized identifiers (`OP-001`, `OP-101`).
- [x] **Operating State vs Task Phase Distinction**:
  - Renamed `"OPERATING PHASE"` label on the hero card to `"OPERATING STATE"`.
  - Mapped machine state strictly to the 4 canonical kinematic states: `IDLE`, `WORKING`, `TRAVELLING`, `STOPPED`.
  - Derived operating state dynamically from real-time telemetry sensor inputs (speed, RPM, state code) over WebSocket.
  - Preserved Task Phase as a decoupled future operational dispatch concept (`DIGGING`, `LOADING`, `DUMPING`). IDLE is never used as a task phase.
- [x] **Machine Header & Co-Pilot Services Refinement**:
  - Preserved clean industrial header: Machine ID, Operator 1, UTC Clock, Edge Status, and WebSocket link indicator.
  - Eliminated internal development jargon (`FUTURE COCKPIT SUBSYSTEMS (PHASE 2 RESERVED)`).
  - Replaced with **"CO-PILOT SERVICES"** showcasing realistic subsystem statuses:
    - `VOICE COPILOT` (`STANDBY`)
    - `ANOMALY ANALYTICS` (`STANDBY`)
    - `IN-CAB MANUALS` (`READY`)
    - `SAFETY ENGINE` (`READY`)
- [x] **Training Hub Foundation (Coach Page)**:
  - Added top-level `COACH` page accessible from top navigation bar and contextual alerts.
  - Built modular frontend training components:
    - `CoachPage.jsx`: Master container routing between library, lesson view, quiz assessment, and history.
    - `TrainingRecommendation.jsx`: Prominent recommendation card highlighting trigger reason and duration.
    - `TrainingLibrary.jsx`: Catalog of structured safety, efficiency, and equipment modules.
    - `TrainingLesson.jsx`: Multi-media viewer supporting HTML5 video with clean fallback notice (`Training media not configured` when physical assets are absent), module briefings, and procedural key points.
    - `TrainingQuiz.jsx`: Interactive 3-question compliance assessment with instantaneous score calculation, passed/failed determination, and API persistence.
    - `TrainingHistory.jsx`: Record of completed operator training sessions with timestamped scores.
  - Integrated compact **`COACHING MOMENT`** card directly on the Command Center cockpit when an active recommendation exists, linking seamlessly to the lesson.
  - Created `frontend/public/training/` asset directory.
- [x] **Training Backend Contracts & APIs**:
  - Created Pydantic schemas in `backend/app/schemas/training.py` (`Lesson`, `QuizQuestion`, `TrainingRecommendation`, `TrainingCompletionRequest`, `TrainingHistoryItem`).
  - Implemented `TrainingService` in `backend/app/training/service.py` with 3 core safety curriculum modules, active recommendation logic, and in-memory completion history.
  - Created REST router in `backend/app/api/training.py` with endpoints:
    - `GET /api/training/recommendations`: Active recommendations for operator.
    - `GET /api/training/lessons`: Available lesson catalog.
    - `GET /api/training/lessons/{id}`: Detailed lesson metadata with 3-question quiz.
    - `GET /api/training/history`: Operator completion logs.
    - `POST /api/training/complete`: Record assessment score and completion status.
  - Mounted `/api/training` in `backend/app/main.py`.
- [x] **Automated Tests & Quality Assurance**:
  - Authored `backend/tests/test_training.py` with 5 tests verifying recommendations, catalog retrieval, lesson detail, quiz grading, and 404 handling.
  - Executed full test suite: **48 passing tests across all components in 3.76s**.
  - Verified bundle build: `npm run build` completed with 0 errors in 1.97s.
  - Verified end-to-end browser user flow via subagent (verified generic operator identity, OPERATING STATE indicator, Co-Pilot Services, Coaching Moment card, lesson viewer, and 100% quiz submission).

### Phase 2.1 Live Telemetry Simulator & WebSocket Streaming
- [x] Built `simulator/scenarios.py` implementing all 7 deterministic scenarios (`normal`, `seatbelt_violation`, `proximity_warning`, `proximity_critical`, `excessive_idle`, `repeated_safety`, `eta_delay`) mapped to `data/synthetic/demo_telemetry.csv`.
- [x] Built `simulator/generator.py` with `TelemetryGenerator` pacing real-time timestamps and maintaining physical monotonicity.
- [x] Built `simulator/client.py` with `SimulatorClient` providing exponential backoff reconnect and standardized logging.
- [x] Built `simulator/replay.py` CLI supporting `--scenario`, `--speed`, `--machine-id`, `--operator-id`, `--loop`.
- [x] Authored comprehensive documentation in `simulator/README.md`.
- [x] Implemented domain services in `backend/app/services/`:
  - `TelemetryService`: canonical Pydantic validation, SQLite storage with duplicate protection, latest snapshot and historical querying.
  - `TelemetryBroadcastService`: thread-safe connection manager, multi-client frontend fan-out, dead-socket pruning.
- [x] Implemented `/ws/telemetry` WebSocket endpoint in `backend/app/edge/telemetry_ws.py` supporting both simulator ingestion and frontend streaming.
- [x] Refactored `backend/app/api/telemetry.py` to use `TelemetryService` and added `GET /api/telemetry/history`.
- [x] Connected React frontend in `frontend/src/services/api.js` (`createTelemetryWebSocket`, `fetchTelemetryHistory`) and `frontend/src/components/OperatorConsole.jsx` (`wsConnected` state, live streaming indicator).
- [x] Created `backend/tests/test_telemetry_ws.py` with 11 automated unit and integration tests (ingestion, SQLite storage, duplicate protection, malformed JSON, validation error, ping-pong, multi-client broadcast, simulator disconnect).
- [x] Executed full test suite with **43 passing tests across all components in 3.34s**.
- [x] Verified live streaming with browser subagent on `http://localhost:5173/` (`WS: LIVE` indicator verified).

### Phase 2.0 Architecture Baseline
- [x] Authored comprehensive production-like prototype architecture in `ARCHITECTURE.md` (394 lines, 4 core pipelines, safety matrix, sequence diagrams).
- [x] Codified the **Non-Negotiable Safety Invariants**:
  1. Edge Safety Engine is 100% deterministic and local.
  2. ML is never required for immediate cab safety.
  3. LLM must never decide safety, change severity, suppress alerts, or override safety engine.
  4. Local-first offline baseline operates with zero degradation during network drops.
- [x] Delineated engineering ownership: Full-stack engineer owns frontend, backend, edge safety, simulator, alert state machine, sync, voice, LLM/RAG, and containerization. Teammates own ONLY ML model training and evaluation.
- [x] Implemented decoupled ML interface contracts in `backend/app/ml/interfaces.py` (`AnomalyPredictor`, `ETAPredictor`, `AnomalyResult`, `ETAResult`) using abstract base classes and Pydantic v2 schemas.
- [x] Scaffolded modular directory layout under `backend/app/`: `api/`, `edge/`, `cloud/`, `database/`, `schemas/`, `services/`, `ml/`, `copilot/`, `training/`, `sync/`, `simulator/`.
- [x] Updated `MEMORY.md` and `IMPLEMENTATION.md` to reflect Phase 2.0 baseline and ownership boundaries.
- [x] Confirmed zero regression on Phase 1: all 32 pytest tests pass in 1.28s, frontend Vite build passes cleanly.

### Phase 1 Core Deliverables (Preserved & Verified)
- [x] Full repository audit and environment discovery (PowerShell, Python 3.12.0, Node.js v24.19.0, npm 11.17.0).
- [x] Defined complete domain data schema (Machines, Operators, Telemetry Logs, Alerts, Shift Cycles).
- [x] Implemented `scripts/generate_synthetic_data.py` with deterministic seed (`SEED = 42`) and causal physical relationships.
- [x] Generated `task_history.csv` (150 rows), `telemetry_history.csv` (3,200 rows), `demo_telemetry.csv` (51 rows).
- [x] Executed validation suite with **56,119 automated checks passing with 0 errors and 0 warnings**.
- [x] Implemented SQLite database connection, 8 SQLAlchemy models, and idempotent data loader.
- [x] Implemented Pydantic v2 request/response schemas matching datasets exactly.
- [x] Built REST API endpoints (`/health`, `/api/telemetry/latest`, `/api/telemetry`, `/api/tasks`, `/api/tasks/{task_id}`, `/api/machines`, `/api/operators`).
- [x] Created pytest test suite with **32 automated tests passing cleanly in 1.28s**.
- [x] Initialized React 19 + Vite 8 frontend project in `frontend/` with industrial dark cockpit styling.
- [x] Created reusable UI components (`MachineHeader`, `CurrentTask`, `MachineMetrics`, `SafetyPanel`, `TaskPanel`, `SystemStatus`, `TelemetryValue`, `OperatorConsole`).
- [x] Built production bundle with `npm run build` (1887 modules transformed, 0 errors, 1.3s).
- [x] Verified full live frontend-backend integration over localhost.

---

## 3. Pending Implementation Roadmap
- [ ] **Phase 2.1: Telemetry Simulator & WebSocket Streaming**
  - Implement CAN bus / J1939 simulator daemon in `backend/app/simulator/`
  - Build WebSocket streaming endpoints in `backend/app/edge/` and `backend/app/api/`
  - Connect live streaming to React operator console
- [ ] **Phase 2.2: Deterministic Edge Safety Engine & Alert State Machine**
  - Implement rule engine in `backend/app/edge/` (seatbelt interlock, radar distance, thermal envelope)
  - Implement alert state machine (`ACTIVE` -> `ACKNOWLEDGED` -> `CLEARED`)
  - Incident recording and local audit logging
- [ ] **Phase 2.3: Local-First Sync Outbox & Cloud Sync**
  - Implement transactional outbox in `backend/app/sync/`
  - Offline network detection and resilient replay
  - Cloud PostgreSQL integration and sync endpoints in `backend/app/cloud/`
- [ ] **Phase 2.4: In-Cab Voice & Copilot (Intent Router + RAG)**
  - Deterministic intent router in `backend/app/copilot/`
  - In-cab RAG retrieval over CAT operator manuals
  - Guardrailed LLM response synthesis
- [ ] **Phase 2.5: ML Model Ingestion**
  - Integrate teammate model implementations for `AnomalyPredictor` and `ETAPredictor`
- [ ] **Phase 2.6: Operator Training System**
  - Shift scoring and cycle optimization feedback in `backend/app/training/`
- [ ] **Phase 2.7: Containerization & Cloud Deployment**
  - Multi-stage Dockerfile and Docker Compose

---

## 4. Files Created
| File Path | Description | Size / Count |

|---|---|---|
| `MEMORY.md` | Core project memory, system boundaries, schemas, API contracts, and constraints. | ~10 KB |
| `IMPLEMENTATION.md` | Implementation plan, milestone tracking, commands, and test logs. | Active |
| `DATA_DICTIONARY.md` | Detailed schema, physical units, types, and bounds for all synthetic datasets. | ~6 KB |
| `scripts/generate_synthetic_data.py` | Deterministic synthetic generator for tasks, telemetry, and demo scenarios. | ~20 KB |
| `scripts/load_data.py` | Reusable data loader and comprehensive validation engine. | ~15 KB |
| `data/raw/.gitkeep` | Raw data directory placeholder for external logs. | 0 bytes |
| `data/processed/.gitkeep` | Processed data directory placeholder for transformed features. | 0 bytes |
| `data/synthetic/task_history.csv` | Synthetic task orders with causal delay factors. | 150 rows, 19.3 KB |
| `data/synthetic/telemetry_history.csv` | Primary 8-hour, 45s interval telemetry time-series across 5 CAT machines. | 3,200 rows, 486 KB |
| `data/synthetic/demo_telemetry.csv` | Deterministic sequences for judging & demonstration scenarios. | 51 rows, 8.8 KB |

| `backend/requirements.txt` | Python dependencies (FastAPI, SQLAlchemy, Pandas, etc.) | ~230 bytes |
| `backend/.env.example` / `.env` | Environment configuration (hosts, ports, db path, CORS) | ~250 bytes |
| `backend/app/config.py` | Pydantic BaseSettings with dynamic CORS parsing | ~1 KB |
| `backend/app/database/connection.py` | SQLite thread-safe engine & session generator | ~1 KB |
| `backend/app/database/models.py` | 8 SQLAlchemy tables (`telemetry`, `tasks`, + 6 extension tables) | ~8 KB |
| `backend/app/database/init_db.py` | Idempotent table creator & synthetic CSV loader | ~5.5 KB |
| `backend/app/schemas/common.py` | Pydantic response models: Health, Machine, Operator | ~1 KB |
| `backend/app/schemas/telemetry.py` | Pydantic TelemetryResponse matching 19-column CSV | ~1.5 KB |
| `backend/app/schemas/task.py` | Pydantic TaskResponse matching 12-column CSV | ~1 KB |
| `backend/app/api/health.py` | `GET /health` connectivity check | ~1 KB |
| `backend/app/api/telemetry.py` | `GET /api/telemetry/latest`, `GET /api/telemetry` | ~3 KB |
| `backend/app/api/tasks.py` | `GET /api/tasks`, `GET /api/tasks/{task_id}` | ~2 KB |
| `backend/app/api/machines.py` | `GET /api/machines` fleet summary | ~1.8 KB |
| `backend/app/api/operators.py` | `GET /api/operators` operator summary | ~1.8 KB |
| `backend/app/ml/interfaces.py` | Decoupled ML interfaces & Pydantic contracts (`AnomalyPredictor`, `ETAPredictor`) | ~4.7 KB |
| `backend/app/ml/__init__.py` | ML module exports for anomaly and ETA contracts | ~500 bytes |
| `backend/app/services/__init__.py` | Domain services package initialization | ~200 bytes |
| `backend/app/services/telemetry_service.py` | TelemetryService domain logic (validation, duplicate detection, DB persistence) | ~4 KB |
| `backend/app/services/broadcast_service.py` | TelemetryBroadcastService multi-client WebSocket connection manager | ~3.3 KB |
| `backend/app/edge/telemetry_ws.py` | High-frequency `/ws/telemetry` WebSocket endpoint | ~4.5 KB |
| `backend/app/sync/__init__.py` | Sync outbox & cloud sync package initialization | ~200 bytes |
| `backend/app/simulator/__init__.py` | Telemetry simulator package initialization | ~200 bytes |
| `backend/app/main.py` | FastAPI application entrypoint with lifespan auto-seed & CORS | ~2 KB |
| `simulator/scenarios.py` | 7 deterministic scenario definitions & demo_telemetry.csv loader | ~4.5 KB |
| `simulator/generator.py` | Real-time timestamp pacer & monotonic telemetry generator | ~2.5 KB |
| `simulator/client.py` | Resilient WebSocket client with backoff and [SIMULATOR] logging | ~3 KB |
| `simulator/replay.py` | Replay CLI entrypoint (--scenario, --speed, --machine-id, --loop) | ~4.5 KB |
| `simulator/README.md` | Replay simulator documentation, CLI guide, and WS contracts | ~4 KB |
| `backend/tests/test_telemetry_ws.py` | 11 automated unit and integration tests for WS and simulator | ~7 KB |
| `ARCHITECTURE.md` | Full production-like prototype architecture (4 pipelines, invariants, sequence diagrams, failure matrix) | ~25 KB |
| `frontend/package.json` | React 19, Vite 8, Tailwind CSS v4, Lucide React | ~500 bytes |
| `frontend/vite.config.js` | Vite config with @tailwindcss/vite & API proxy | ~400 bytes |
| `frontend/index.html` | Dark viewport and Google Fonts (Inter, Space Grotesk) | ~1 KB |
| `frontend/src/index.css` | Industrial graphite cockpit design system & glass tokens | ~3 KB |
| `frontend/src/services/api.js` | API client with timeout & graceful offline fallback | ~3.5 KB |
| `frontend/src/components/MachineHeader.jsx` | Header, machine selector, operator ID, edge status | ~4 KB |
| `frontend/src/components/CurrentTask.jsx` | Active task hero, ETA countdown, cycle phase | ~4 KB |
| `frontend/src/components/MachineMetrics.jsx` | 8-metric telemetry grid with semantic thresholds | ~4.5 KB |
| `frontend/src/components/SafetyPanel.jsx` | Seatbelt interlock & radar proximity meter | ~4.5 KB |
| `frontend/src/components/TaskPanel.jsx` | Planned vs predicted duration, next queued task | ~3.5 KB |
| `frontend/src/components/SystemStatus.jsx` | Edge hardware integrity & future phase placeholders | ~4 KB |
| `frontend/src/components/TelemetryValue.jsx` | Reusable tactile industrial telemetry widget | ~2.5 KB |
| `frontend/src/components/OperatorConsole.jsx` | Root cockpit layout, live API polling, error boundary | ~5 KB |
| `frontend/dist/` | Production build artifacts (`npm run build`) | ~292 KB |

---

## 5. Development & Startup Commands

### 5.1 Backend Service
```powershell
# 1. Initialize SQLite Database & Seed from CSVs (Idempotent)
python -m backend.app.database.init_db

# 2. Run Test Suite (32 tests across all endpoints and schemas)
python -m pytest

# 3. Start FastAPI Server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.2 Frontend Operator Console
```powershell
# 1. Install frontend packages
cd frontend
npm install

# 2. Build for production (verifies 0 build errors)
npm run build

# 3. Start development server
npm run dev
```

---

### 5.3 Live Telemetry Simulator
```powershell
# Replay nominal scenario at 1Hz (1 tick/sec)
python simulator/replay.py --scenario normal

# Replay critical proximity alert at 2x speed
python simulator/replay.py --scenario proximity_critical --speed 2.0

# Replay seatbelt violation for specific machine
python simulator/replay.py --scenario seatbelt_violation --machine-id CAT-797F-101

# Continuous loop mode for live demo / judging
python simulator/replay.py --scenario normal --loop --speed 1.0
```

---

## 6. Tests & Validation Strategy
1. **Database Schema & Seeding**:
   - `test_database.py`: Verifies existence of all 8 tables, correct columns on `telemetry` (19) and `tasks` (12), primary keys, and foreign keys.
2. **Schema & Contract Validation**:
   - `test_schemas.py`: Verifies Pydantic validation on valid payloads, missing fields, and type coercion.
3. **Endpoints & Query Filtering**:
   - `test_health.py`: Verifies `GET /health` returns `{status: "ok", service: "shiftguard-edge", database: "connected"}`.
   - `test_telemetry.py`: Verifies fleet snapshot, single machine lookup, 404 handling, multi-field filtering (`machine_id`, `operator_id`, `task_id`, `start_time`, `end_time`), and invalid limit/offset rejection (422).
   - `test_tasks.py`: Verifies task listing, filtering by machine/operator/type, single task lookup, 404 handling, and machines/operators endpoints.
4. **WebSocket & Simulator Streaming**:
   - `test_telemetry_ws.py`: Verifies `/ws/telemetry` ingestion, Pydantic schema validation, SQLite storage with duplicate protection, frontend initial snapshot delivery, malformed JSON handling, ping/pong keepalive, multi-client broadcast fan-out, dead socket cleanup, and 7 scenario definitions.
5. **Training Hub Contracts & Grader**:
   - `test_training.py`: Verifies recommendations query, lesson catalog listing, individual lesson details with 3-question quiz, completion grading, and 404 error handling.
6. **Test Run Result**:
   - **48 passed in 3.76s**, 0 failures.

---

## 7. Known Limitations & Next Steps
- **Safety Decision Engine**: Edge safety rules (proximity radar interlock, seatbelt motion interlock, thermal boundaries) and the Alert State Machine (`ACTIVE` -> `ACKNOWLEDGED` -> `CLEARED`) will be implemented in Phase 2.2.
- **Offline Sync Outbox**: Local outbox queue and cloud sync daemon are scheduled for Phase 2.3.
- **ML Models**: ML models are intentionally decoupled behind abstract contracts (`AnomalyPredictor`, `ETAPredictor`) and will be implemented by data science teammates.
