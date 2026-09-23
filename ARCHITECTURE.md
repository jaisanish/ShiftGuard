# ShiftGuard — Full Application Architecture (Phase 2.0 Baseline)

---

## 1. Executive Summary & System Philosophy

ShiftGuard is an intelligent, ruggedized edge-to-cloud operator assistant for Caterpillar (CAT) heavy earthmoving and mining machinery. It pairs real-time, deterministic in-cab safety intelligence with local-first telemetry persistence, voice interaction, predictive cycle analytics, and cloud fleet synchronization.

### The Zero-Harm Architectural Imperative
In heavy earthmoving and open-pit mining environments (involving 400-tonne haul trucks, hydraulic shovels, and dozers operating near sheer pit walls and dynamic blast benches), safety cannot depend on nondeterministic networks, cloud latency, or probabilistic AI models.

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

## 2. Global System Architecture

```text
+-----------------------------------------------------------------------------------------------+
|                                    SHIFTGUARD PLATFORM                                       |
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|  [ PIPELINE 1: REAL-TIME TELEMETRY & EDGE SAFETY LOOP ]                                      |
|  Synthetic CSV / Simulator  -->  WebSocket Stream  -->  FastAPI Edge Ingest                   |
|                                                               │                               |
|                                                        Validation Engine                      |
|                                                               │                               |
|                                                      Deterministic Safety                     |
|                                                               │                               |
|                                                      Alert State Machine                      |
|                                                               │                               |
|                                                      SQLite (shiftguard.db)                   |
|                                                               │                               |
|                                                    Real-time WS Events                        |
|                                                               │                               |
|                                                    React Operator Console                     |
|                                                                                               |
|  [ PIPELINE 2: EDGE-TO-CLOUD & ML ANALYTICS LOOP ]                                           |
|  Local SQLite Events  -->  Sync Outbox Queue  -->  Cloud Sync Client  -->  Cloud PostgreSQL  |
|                                                                                  │            |
|                                                                           Fleet Analytics     |
|                                                                                  │            |
|                                                                           ML Model Training   |
|                                                                                  │            |
|                                                                         Inference Artifacts   |
|                                                                                  │            |
|                                                                         Operator Insights     |
|                                                                                               |
|  [ PIPELINE 3: IN-CAB VOICE & INTENT COPILOT ]                                               |
|  Cab Microphone  -->  Audio Capture  -->  STT  -->  Intent Router                             |
|                                                          ├── [Telemetry/Tasks] -> Local REST  |
|                                                          └── [Diagnostic/RAG]  -> LLM + RAG   |
|                                                                                         │     |
|                                                                            Synthesized Voice  |
|                                                                                               |
|  [ PIPELINE 4: IN-CAB RAG KNOWLEDGE RETRIEVAL ]                                              |
|  CAT Operation Manuals  -->  Vector Embeddings  -->  Retriever  -->  LLM  -->  Cab Guidance   |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
```

---

## 3. Core Processing Pipelines

### Pipeline 1: Real-Time Telemetry & Safety Loop
High-frequency (1Hz to 10Hz) sensor monitoring ensuring sub-100ms threat detection in the cab.

```text
┌─────────────────────────┐
│ Synthetic CSV / CAN Bus │
└────────────┬────────────┘
             │ J1939 Broadcast
             ▼
┌─────────────────────────┐
│   Telemetry Simulator   │
└────────────┬────────────┘
             │ WebSocket (/ws/telemetry/stream)
             ▼
┌─────────────────────────┐
│  FastAPI Edge Ingestion │
└────────────┬────────────┘
             │ Pydantic Validation
             ▼
┌─────────────────────────┐
│   Edge Safety Engine    │ <--- 100% Deterministic Rule Engine
└────────────┬────────────┘
             │ Safety Events / Boundary Crossings
             ▼
┌─────────────────────────┐
│   Alert State Machine   │ <--- INFO / WARNING / CRITICAL State Lifecycles
└────────────┬────────────┘
             │
      ┌──────┴──────────────────────────┐
      ▼                                 ▼
┌──────────────┐              ┌───────────────────┐
│ SQLite DB    │              │ WS Event Dispatch │
│ (Local Edge) │              └─────────┬─────────┘
└──────────────┘                        │
                                        ▼
                              ┌───────────────────┐
                              │ React Cab Console │
                              └───────────────────┘
```

1. **Telemetry Simulator**: Emulates CAT electronic control modules (ECMs) broadcasting engine RPM, ground speed, hydraulic pressure, temperatures, proximity radar, and seatbelt sensors.
2. **FastAPI Edge Ingestion**: Parses inbound frames, enforces schema constraints, and drops malformed frames with telemetry error metrics.
3. **Safety Engine**: Pure functional evaluation checking:
   - Moving with unfastened seatbelt (`machine_speed_kmh > 0` and `seatbelt_status == 'UNFASTENED'`)
   - Proximity obstacle breach (`proximity_distance_m < 5.0m` critical stop, `< 15.0m` warning)
   - Thermal overload thresholds (`coolant_temp_c > 98°C`, `hydraulic_oil_temp_c > 88°C`)
   - High engine duty abuse (`engine_load_pct > 92%` sustained while stopped)
4. **Alert State Machine**: Deduplicates transient spikes, manages alert lifecycle (`NEW` -> `ACTIVE` -> `ACKNOWLEDGED` -> `RESOLVED`), and handles operator silencing constraints.
5. **Real-Time WebSocket Events**: Broadcasts state changes to the in-cab display with sub-50ms latency.

---

### Pipeline 2: Cloud Sync & Asynchronous Analytics Loop
Local-first edge persistence with guaranteed at-least-once cloud synchronization.

```text
┌────────────────┐     Insert Event      ┌───────────────┐
│ SQLite Database├──────────────────────>│  Sync Outbox  │
│ (shiftguard.db)│                       │ (sync_outbox) │
└────────────────┘                       └───────┬───────┘
                                                 │
                                                 │ Polling / Event-Driven Watcher
                                                 ▼
                                         ┌───────────────┐
                                         │  Sync Client  │
                                         └───────┬───────┘
                                                 │
                                     Offline?    │ Network Available?
                                    ┌────────────┴────────────┐
                                    ▼                         ▼
                              ┌───────────┐             ┌───────────┐
                              │ Hold in   │             │ HTTPS POST│
                              │ Queue     │             │ Batch     │
                              │ (Backoff) │             └─────┬─────┘
                              └───────────┘                   │
                                                              ▼
                                                        ┌───────────┐
                                                        │ Cloud API │
                                                        └─────┬─────┘
                                                              ▼
                                                        ┌───────────┐
                                                        │ Cloud     │
                                                        │ PostgreSQL│
                                                        └─────┬─────┘
                                                              │
                                                        ┌─────┴─────┐
                                                        ▼           ▼
                                                  ┌──────────┐┌───────────┐
                                                  │Fleet BI  ││ML Training│
                                                  │Analytics ││Pipeline   │
                                                  └──────────┘└───────────┘
```

1. **Transactional Outbox**: Any safety event, completed haul cycle, or shift summary is written to `sync_outbox` in the same SQLite transaction as the event itself.
2. **Sync Client (`backend/app/sync/`)**: Periodically drains un-synced outbox records, compresses payloads, and sends them via HTTPS to the cloud endpoint.
3. **Network Resilience**: If the machine enters a pit dead-zone (shadowed by high-walls), the sync client backs off exponentially. No data is lost; upon climbing to the dump crest with LTE/mesh coverage, all queued records flush idempotently.
4. **Cloud Database**: Cloud PostgreSQL acts as the fleet-wide data lake for enterprise dispatchers and ML model training.

---

### Pipeline 3: In-Cab Voice & Natural Language Copilot Loop
Hands-free audio interaction allowing operators to query status without taking hands off hydraulic joysticks.

```text
┌───────────────────────┐
│ Cab Microphone Audio  │
└───────────┬───────────┘
            │ Audio Stream / WAV Chunk
            ▼
┌───────────────────────┐
│ Speech-to-Text (STT)  │ <--- Fast local Whisper / Speech Engine
└───────────┬───────────┘
            │ Transcribed Query String
            ▼
┌───────────────────────┐
│     Intent Router     │
└───────────┬───────────┘
            │
    ┌───────┴───────────────────────────────┐
    │                                       │
    ▼ Deterministic Query                   ▼ Technical Guidance / Manual
┌───────────────────────┐               ┌───────────────────────┐
│ Local Telemetry REST  │               │ RAG Retrieval Engine  │
│ (/api/telemetry/...)  │               └───────────┬───────────┘
└───────────┬───────────┘                           │ Retrieved Chunks
            │                                       ▼
            │ Structured JSON               ┌───────────────────────┐
            │ Metrics                       │ LLM Synthesis Engine  │
            │                               │ (STRICT GUARDRAILS)   │
            │                               └───────────┬───────────┘
            └───────────────────┬───────────────────────┘
                                │ Natural Language Response String
                                ▼
                    ┌───────────────────────┐
                    │ Text-to-Speech (TTS)  │
                    └───────────┬───────────┘
                                │ Audio Output
                                ▼
                    ┌───────────────────────┐
                    │ In-Cab Speaker / HUD  │
                    └───────────────────────┘
```

1. **Intent Classification**:
   - `TELEMETRY_QUERY` ("What is my current coolant temperature?"): Routed **directly to local deterministic REST services**. Zero LLM hallucination risk.
   - `TASK_STATUS` ("How many cycles remaining?"): Routed to `TaskService`.
   - `TECHNICAL_MANUAL` ("What is the procedure for an ENG-042 warning?"): Routed to the RAG knowledge pipeline.
2. **Strict Guardrails**: The LLM synthesizes procedural guidance only. It is architecturally prevented from modifying machine state or silencing safety warnings.

---

### Pipeline 4: In-Cab RAG Knowledge Retrieval Loop
Grounded technical manual search for immediate in-cab diagnostic troubleshooting.

```text
┌─────────────────────────┐
│ CAT Equipment Manuals   │
│ & Maintenance SOPs      │
└────────────┬────────────┘
             │ Document Ingestion & Chunking
             ▼
┌─────────────────────────┐
│ Local Vector Database   │ <--- ChromaDB / FAISS / SQLite-VSS
└────────────┬────────────┘
             │ Semantic Query Similarity
             ▼
┌─────────────────────────┐
│ Top-K Relevant Excerpts │
└────────────┬────────────┘
             │ System Prompt + Context + Machine Fault Code
             ▼
┌─────────────────────────┐
│ Small Language Model    │
└────────────┬────────────┘
             │ Actionable Operator Checklist
             ▼
┌─────────────────────────┐
│ Screen Banner & Audio   │
└─────────────────────────┘
```

---

## 4. Module Ownership & System Boundaries

```text
backend/app/
├── api/          # HTTP REST & WebSocket endpoint routers
├── edge/         # Deterministic safety engine, rule evaluators, alert state machine
├── cloud/        # Cloud sync adapters, cloud database connections, AWS integration
├── database/     # SQLAlchemy connection, SQLite models, table initialization & seeder
├── schemas/      # Pydantic v2 request/response contracts & shared DTOs
├── services/     # Core domain business logic services (telemetry, task, fleet)
├── ml/           # Model interfaces & inference runner adapters (Anomaly, ETA)
├── copilot/      # Audio capture, STT/TTS, intent router, LLM synthesis, RAG retrieval
├── training/     # Training dataset extractors, benchmark evaluators, training logs
├── sync/         # Outbox dispatcher, network detector, exponential backoff retries
└── simulator/    # CAN bus/J1939 simulator, scenario replay, deterministic tick loop
```

### Module Responsibilities Breakdown

| Module | Core Responsibility | Ownership | Phase 1 Status |
|---|---|---|---|
| `backend/app/api/` | Exposes REST & WebSocket routes; enforces input validation; handles CORS. | Full-Stack Engineer | Phase 1 REST Complete |
| `backend/app/edge/` | Pure deterministic safety rules; proximity checks; seatbelt interlock; alert state transitions. | Full-Stack Engineer | Scaffolded (Phase 2.0) |
| `backend/app/cloud/` | Cloud database client; cloud API endpoints; AWS S3/PostgreSQL connectors. | Full-Stack Engineer | Scaffolded (Phase 2.0) |
| `backend/app/database/` | SQLite database connection; 8 table models; idempotent migration & seeding. | Full-Stack Engineer | Complete (Phase 1) |
| `backend/app/schemas/` | Pydantic v2 models for telemetry, tasks, alerts, and system health. | Full-Stack Engineer | Complete (Phase 1) |
| `backend/app/services/` | Business logic services orchestrating queries and decoupling routers from ORM. | Full-Stack Engineer | Scaffolded (Phase 2.0) |
| `backend/app/ml/` | Abstract model interfaces (`AnomalyPredictor`, `ETAPredictor`) & inference runner. | Full-Stack (Interface) / ML Engineers (Models) | Contracts Created |
| `backend/app/copilot/` | STT, Intent Router, LLM prompt engineering, RAG manual vector store, TTS. | Full-Stack Engineer | Scaffolded (Phase 2.0) |
| `backend/app/training/` | Training record persistence, feature extraction, evaluation metrics logging. | Full-Stack Engineer | Scaffolded (Phase 2.0) |
| `backend/app/sync/` | Local outbox polling, network status detection, idempotent batch upload. | Full-Stack Engineer | Scaffolded (Phase 2.0) |
| `backend/app/simulator/` | CAN bus / J1939 simulator streaming synthetic CSVs over WebSocket at 1Hz. | Full-Stack Engineer | Scaffolded (Phase 2.0) |
| `frontend/` | React 19 + Tailwind CSS operator console, telemetry widgets, safety alerts HUD. | Full-Stack Engineer | Complete (Phase 1) |

---

## 5. Machine Learning Integration Contracts

ML engineers develop, train, and benchmark models independently. They implement the stable abstract base classes defined in `backend/app/ml/interfaces.py`.

### 5.1 Anomaly Detection Interface (`AnomalyPredictor`)

```python
class AnomalyPredictor(ABC):
    @abstractmethod
    def predict(self, telemetry_record: Dict[str, Any]) -> AnomalyResult:
        """
        Evaluate a single telemetry reading for physical sensor anomalies.
        Returns:
            AnomalyResult(
                machine_id=...,
                timestamp=...,
                is_anomaly=True/False,
                anomaly_score=0.0-1.0,
                affected_sensors=['coolant_temp_c', 'hydraulic_pressure'],
                sensor_scores={'coolant_temp_c': 0.88},
                confidence=0.95,
                model_version='isolation_forest_v1.2'
            )
        """
        pass

    @abstractmethod
    def batch_predict(self, telemetry_window: List[Dict[str, Any]]) -> List[AnomalyResult]:
        """Evaluate a rolling time-series window."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns True if weights are loaded and ready."""
        pass
```

### 5.2 ETA Prediction Interface (`ETAPredictor`)

```python
class ETAPredictor(ABC):
    @abstractmethod
    def predict_eta(
        self,
        task_data: Dict[str, Any],
        telemetry_snapshot: Dict[str, Any],
    ) -> ETAResult:
        """
        Predict remaining haul cycle / work order duration.
        Returns:
            ETAResult(
                task_id=...,
                machine_id=...,
                predicted_remaining_min=42.5,
                predicted_total_duration_min=54.2,
                confidence_score=0.91,
                model_version='gradient_boost_eta_v2.0',
                feature_contributions={'weather_factor': +5.2, 'skill_factor': -3.1}
            )
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns True if model weights are loaded."""
        pass
```

---

## 6. Safety & Failure Modes Matrix

| Component Failure | Consequence | Automatic Architectural Defense |
|---|---|---|
| **Cloud Disconnection / Outage** | Zero cloud telemetry sync. | Edge node continues full operation. Events queue in `sync_outbox`. System status flips to `CLOUD: NOT CONNECTED`. Zero cab feature loss. |
| **LLM Service Timeout / Crash** | Voice copilot cannot synthesize technical manuals. | Intent router detects timeout; returns fallback deterministic message: *"Manual service offline. Review physical SOP."* Safety engine is unaffected. |
| **ML Anomaly Model Crash** | Predictive anomaly scoring halts. | Catch block logs model exception; continues edge telemetry ingestion. Safety engine handles physical threshold violations deterministically. |
| **WebSocket Connection Drop** | Frontend loses live stream. | Frontend automatically polls REST `/api/telemetry/latest` every 3 seconds as a fallback until the WebSocket reconnects. |
| **Sensor Value Corruption** | Impossible telemetry values (e.g. negative speed). | Pydantic validation rejects the frame; writes diagnostic advisory `SENS-INVALID-FRAME`; alerts operator. |

---

## 7. Phase Progression & Roadmap Status

1. **Phase 1 — Core Platform & Data Schemas**: [COMPLETED]
   Database schema, seed data loader, REST APIs, and foundational UI.
2. **Phase 2 — Telemetry Simulator & WebSocket Streaming**: [COMPLETED]
   Duplex WebSocket streaming pipeline, CAN-bus / J1939 emulation, scenarios generator.
3. **Phase 3 — Deterministic Edge Safety Engine**: [COMPLETED]
   Local deterministic rules (`SeatbeltSafetyRule`, `ProximitySafetyRule`), context buffering.
4. **Phase 4 — Complete Realtime Operator Console**: [COMPLETED]
   Live WebSocket streaming to React cockpit with zero refresh, strict zero-fabricated ETA invariant, authoritative operating states, critical alert modal overlay, incident audit trails & physical context buffer inspection, multi-page routing.
5. **Phase 5 — Cloud Backend & Offline Sync**: [COMPLETED]
6. **Phase 6 — Anomaly Model Pipeline Integration**: [COMPLETED]
7. **Phase 7 — ETA Model Pipeline Integration**: [UPCOMING]
8. **Phase 8 — Voice & In-Cab Copilot / Manual RAG**: [UPCOMING]

---

## 8. Phase 4 Architecture — Realtime Operator Console & Incident Context Buffers

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 4 OPERATOR CONSOLE ARCHITECTURE                            │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                           │
│   CAN-Bus Simulator ─────► ws://host:8000/ws/telemetry?role=simulator                    │
│                                    │                                                      │
│                                    ▼                                                      │
│                        [Telemetry Ingestion Pipeline]                                     │
│                        1. Pydantic Schema Validation                                      │
│                        2. Persistence to SQLite (TelemetryModel)                          │
│                        3. EdgeSafetyEngine.evaluate_telemetry()                           │
│                           ├── Rolling 60s Context Buffer                                  │
│                           ├── SeatbeltSafetyRule (Speed + Latched)                        │
│                           └── ProximitySafetyRule (Radar + Dynamic Stopping)              │
│                        4. Persistence to SQLite (AlertModel, IncidentModel)               │
│                        5. Canonicalize State: to_canonical_operating_state()                │
│                                    │                                                      │
│                                    ▼ Broadcast (JSON)                                     │
│   ┌────────────────────────────────┴─────────────────────────────────┐                    │
│   │  "telemetry_update"      │ "safety_update" │ "incident_created"  │                    │
│   └────────────────────────────────┬─────────────────────────────────┘                    │
│                                    │                                                      │
│                                    ▼                                                      │
│                   ws://host:8000/ws/telemetry?role=frontend                               │
│                                    │                                                      │
│                                    ▼                                                      │
│                        [RealtimeContext.jsx]                                              │
│                        - Single persistent WebSocket connection                           │
│                        - Initial snapshot sync: "telemetry_initial"                       │
│                        - Rolling 50-point History (Speed, RPM, Load, Prox)                │
│                        - Authoritative Safety & Alerts State                              │
│                        - Incident Toast Notifications                                     │
│                                    │                                                      │
│           ┌────────────────────────┼────────────────────────┐                             │
│           ▼                        ▼                        ▼                             │
│  [Command Center Tab]     [Incidents Tab]           [Safety Tab]                          │
│  - Critical Alert Overlay - Incident Registry       - Deterministic Rules Badge           │
│  - Incident Toast Banner  - Context Buffer Modal    - Interlock Status Cards              │
│  - Strict "MODEL PENDING"   (Pre/Trigger/Post)      - Active / Recent Alert Logs          │
│  - Rolling SVG Sparklines - Operator Acknowledge    - Acknowledge Actions                 │
│  - Authoritative State                                                                    │
│  - "Ask ShiftGuard" Voice                                                                 │
│                                                                                           │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Phase 6 Advisory Analytics Architecture

```text
Telemetry history ──► 15-minute causal feature windows ──► RobustScaler
                                                              │
                                                              ▼
                                                       Isolation Forest
                                                              │
                         operator baseline / global fallback ◄─┤
                                                              ▼
                                                score + evidence + type
                                                              │
                                ┌─────────────────────────────┴──────────────┐
                                ▼                                            ▼
                        SQLite anomalies                              React Insights
                                │
                                ▼
                        Sync Outbox (ANOMALY)
                                │
                                ▼
                      Cloud anomaly history API
```

Phase 6 is downstream analytics only. `EdgeSafetyEngine` never imports the anomaly package, never waits for inference, and never uses an anomaly result to determine severity. Missing or invalid model artifacts degrade only the Insights surfaces.
