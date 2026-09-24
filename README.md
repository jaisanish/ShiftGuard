# ShiftGuard — Smart Operator Assistant for CAT Machinery

> **DISCLAIMER:**  
> All data and telemetry generated, stored, and displayed in this project is **100% SYNTHETIC** and programmatically generated for demonstration, testing, and development of the ShiftGuard Operator Assistant. It does **NOT** represent actual Caterpillar Inc. production data, machine telemetry, or operational records.

---

## 1. Overview
ShiftGuard is an intelligent, ruggedized in-cab operator assistant and telemetry intelligence platform designed for Caterpillar heavy earthmoving and mining machinery (such as CAT 797F Haul Trucks, CAT 6060 Hydraulic Mining Shovels, CAT 994K Wheel Loaders, and CAT D11 Track Dozers).

The system provides real-time in-cab situational awareness, machinery health monitoring, haul cycle productivity tracking, and safety alert visibility under tough operating conditions.

---

## 2. Architecture (Phase 1 Baseline)

ShiftGuard is architected as a modular, local-first distributed edge platform:

```text
┌────────────────────────────────────────────────────────┐
│                   ShiftGuard System                    │
└────────────────────────────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Data Layer  │    │ Backend Node │    │ Cab Console  │
│  (Synthetic) │    │  (FastAPI)   │    │ (React+Vite) │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
  CSV Datasets         SQLite DB           Industrial
  - Telemetry          (8 Tables)          Dark Cockpit
  - Tasks              REST /api/v1        Tactile HUD
```

- **Data Layer**: Deterministic synthetic generators modeling realistic CAT machinery physics and operational cycles.
- **Persistence**: SQLite database (`shiftguard.db`) with 8 tables (telemetry, tasks, alerts, incidents, anomalies, eta_predictions, training_records, sync_outbox).
- **Backend Service**: High-performance FastAPI REST API providing data contracts and health checks.
- **Operator Console**: Cinematic, minimal industrial React + Tailwind CSS dashboard optimized for in-cab touch displays.

---

## 3. Quickstart & Setup Guide

### Prerequisites
- **Python**: 3.12+
- **Node.js**: 20+ (Node v24 tested)
- **PowerShell / Terminal**

### Step 1: Clone and Setup Backend
```powershell
# Install Python backend dependencies
pip install -r backend/requirements.txt
```

### Step 2: Generate Synthetic Datasets
```powershell
# Generates 3,200 telemetry logs, 150 tasks, and 51 demo scenario records
python scripts/generate_synthetic_data.py

# Validate generated datasets against physical bounds and schema integrity
python scripts/load_data.py
```

### Step 3: Initialize Database & Seed
```powershell
# Idempotently creates SQLite tables and seeds from synthetic datasets
python -m backend.app.database.init_db
```

### Step 4: Run Backend Test Suite
```powershell
# Run the 32 automated tests
python -m pytest
```

### Step 5: Start Backend Server
```powershell
# Starts FastAPI server on http://localhost:8000
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### Step 6: Setup & Start Frontend Console
In a new terminal window:
```powershell
cd frontend

# Install frontend dependencies
npm install

# Build production bundle (verifies zero compile errors)
npm run build

# Start Vite dev server on http://localhost:5173
npm run dev
```

Visit **`http://localhost:5173`** in your browser to interact with the ShiftGuard Operator Console.

---

## 4. API Endpoints

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/health` | None | Service & database connectivity check (`{"status": "ok", "service": "shiftguard-edge", "database": "connected"}`) |
| `GET` | `/api/telemetry/latest` | `machine_id` (optional) | Latest telemetry snapshot for one machine or all fleet machines |
| `GET` | `/api/telemetry` | `machine_id`, `operator_id`, `task_id`, `start_time`, `end_time`, `limit`, `offset` | Historical telemetry time-series query with pagination |
| `GET` | `/api/tasks` | `machine_id`, `operator_id`, `task_type`, `limit`, `offset` | List dispatched work order assignments |
| `GET` | `/api/tasks/{task_id}` | Path parameter | Detailed work order task by ID |
| `GET` | `/api/machines` | None | Fleet overview with latest state, speed, fuel, and hours |
| `GET` | `/api/operators` | None | Operator roster with qualification tier and active machine |

---

## 5. Repository Structure

```text
ShiftGuard/
├── MEMORY.md                          # Architecture memory & technical decisions
├── IMPLEMENTATION.md                  # Milestone tracking, test logs, commands
├── DATA_DICTIONARY.md                 # Column-by-column schema and units dictionary
├── PHASE1_HANDOFF.md                  # Teammate handoff specifications for Phases 2-13
├── README.md                          # Project overview and setup documentation
├── pytest.ini                         # Pytest configuration
├── data/
│   ├── raw/                           # Raw field data placeholder
│   ├── processed/                     # Feature transformation placeholder
│   └── synthetic/                     # Generated CSV datasets
│       ├── task_history.csv
│       ├── telemetry_history.csv
│       └── demo_telemetry.csv
├── scripts/
│   ├── generate_synthetic_data.py    # Deterministic synthetic data generator (Seed 42)
│   └── load_data.py                  # Dataset loader & 56,119-rule validation suite
├── backend/
│   ├── requirements.txt
│   ├── .env / .env.example
│   ├── shiftguard.db                 # SQLite database instance
│   ├── app/
│   │   ├── main.py                   # FastAPI entrypoint, lifespan auto-seed & CORS
│   │   ├── config.py                 # Pydantic BaseSettings
│   │   ├── api/                      # REST endpoints (health, telemetry, tasks, machines, operators)
│   │   ├── database/                 # SQLAlchemy connection, models, init_db
│   │   ├── schemas/                  # Pydantic v2 response contracts
│   │   └── edge/, cloud/, ml/, copilot/, training/  # Reserved future module directories
│   └── tests/                        # 32 pytest unit and integration tests
└── frontend/                         # Vite + React 19 + Tailwind CSS operator console
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── index.css                 # Industrial cockpit dark styling & glass tokens
        ├── services/api.js           # API client with graceful offline fallback
        └── components/               # MachineHeader, CurrentTask, MachineMetrics, etc.
```

---

## 6. Phase Ownership & Future Subsystems

The active delivery sequence is:

- **Phase 2**: Telemetry simulator daemon & WebSocket streaming
- **Phase 3**: Edge safety decision engine
- **Phase 4**: Advanced operator console integration
- **Phase 5**: Cloud backend and offline sync (complete)
- **Phase 6**: Anomaly detection ML (complete)
- **Phase 7**: Cycle ETA ML (complete)
- **Phase 8**: Multimodal voice, LLM and RAG (complete)
- **Phase 9**: Closed-loop operator coaching (complete)
- **Phase 10**: Full integration and production hardening (complete)
- **Phase 11**: Deterministic demonstration mode (complete)
- **Phase 12**: Docker deployment (complete)
- **Phase 13**: AWS cloud deployment (intentionally skipped — not required for local delivery)
- **Phase 14**: Final audit and judging package (complete)

---

## Phase 6 — Advisory Anomaly Analytics (Implemented)

Phase 6 is implemented end-to-end: six causal 15-minute behavioral features, operator-specific baselines with global fallback, a versioned Isolation Forest artifact, local and cloud persistence, REST APIs, and Command Center/Insights UI integration. Safety remains deterministic and independent from the model.

```bash
# Reproduce the checked-in model artifact and diagnostics
python scripts/train_anomaly.py

# Verify backend and frontend
python -m pytest -q
cd frontend
npm run build
npm run lint
```

Important endpoints include `/api/anomalies/model/health`, `/api/anomalies/latest-inference`, `/api/anomalies`, `/api/operators/{operator_id}/baseline`, and `/api/cloud/anomalies`. See [ANOMALY_MODEL.md](ANOMALY_MODEL.md) for feature definitions, artifact handling, diagnostics, limitations, and API details.
