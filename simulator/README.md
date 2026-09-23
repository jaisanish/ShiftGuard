# ShiftGuard Telemetry Replay Simulator

High-fidelity CAN Bus / J1939 telemetry replay simulator designed for demonstrating and evaluating the **ShiftGuard Smart Operator Assistant**.

Streams live, paced sensor frames to the FastAPI edge ingestion service (`/ws/telemetry`) over WebSockets.

---

## 1. Architecture Flow

```text
data/synthetic/demo_telemetry.csv
               ↓
    Python Replay Simulator (simulator/replay.py)
               ↓
    WebSocket (/ws/telemetry)
               ↓
      FastAPI Edge Ingest
               ↓
       TelemetryService (Pydantic Schema Validation)
               ↓
       SQLite Database (shiftguard.db Persistence)
               ↓
    TelemetryBroadcastService (Multi-Client Broadcaster)
               ↓
    React In-Cab Operator Console (Sub-100ms Live Telemetry)
```

---

## 2. Deterministic Scenario Catalog

All scenarios are 100% deterministic and mapped to validated sequences in `data/synthetic/demo_telemetry.csv`:

| Scenario Name | Demo Task ID | Description | Key Telemetry Values |
|---|---|---|---|
| `normal` | `TSK-DEMO-01` | Nominal loaded hauling on haul road north with nominal separation (42m) and zero faults. | Speed: 32.5 km/h, Belt: FASTENED, Dist: 42.0m, Fault: NONE |
| `seatbelt_violation` | `TSK-DEMO-02` | Safety violation: Haul truck at 26.0 km/h with unfastened seatbelt. | Speed: 26.0 km/h, Belt: UNFASTENED, Fault: SEC-SBLT-WARN |
| `proximity_warning` | `TSK-DEMO-03` | Amber warning: Spotting at crusher feed with distance closing to 8.2m. | Speed: 14.0 km/h, Dist: 15.2m → 8.2m, Fault: PRX-WARN-AMBER |
| `proximity_critical` | `TSK-DEMO-04` | Critical alarm: Dangerously close obstacle (<3m) causing emergency stop. | Speed: 11.0 → 0.0 km/h, Dist: 6.5m → 2.8m, Fault: PRX-CRIT-RED |
| `excessive_idle` | `TSK-DEMO-05` | Productivity alert: Wheel loader idling continuously past 30 minutes in staging bay. | Speed: 0.0 km/h, Idle: 24.5m → 35.0m, Fault: IDL-EXCESS-WARN |
| `repeated_safety` | `TSK-DEMO-06` | Compound hazard: Dozer unfastened belt in severe terrain with 4.8m proximity. | Speed: 32.0 → 0.0 km/h, Belt: UNFASTENED, Dist: 4.8m |
| `eta_delay` | `TSK-DEMO-07` | Cycle delay: Haul truck on muddy steep ramp, 95.5% engine load, speed 6.8 km/h. | Speed: 6.8 km/h, Load: 95.5%, Terrain: MUDDY |

---

## 3. CLI Command Usage

### Basic Single-Pass Replay
```bash
# Replay nominal scenario at 1Hz (1 tick/sec)
python simulator/replay.py --scenario normal

# Replay seatbelt violation scenario
python simulator/replay.py --scenario seatbelt_violation

# Replay critical proximity collision alert
python simulator/replay.py --scenario proximity_critical
```

### Custom Machine ID & Speed Multipliers
```bash
# Target specific machine and replay at 2x speed (0.5s ticks)
python simulator/replay.py --scenario proximity_warning --speed 2.0 --machine-id CAT-797F-101

# Replay at 5x speed for rapid stress testing
python simulator/replay.py --scenario repeated_safety --speed 5.0
```

### Continuous Looping Demo Mode
```bash
# Run continuous loop for live judging / cab demonstration
python simulator/replay.py --scenario normal --loop --speed 1.0
```

---

## 4. WebSocket Contract

### Ingestion Request (`simulator` -> `/ws/telemetry`)
Sent as JSON text frame:
```json
{
  "timestamp": "2026-09-23T18:15:30Z",
  "machine_id": "CAT-797F-101",
  "operator_id": "OP-101",
  "engine_hours": 8430.04,
  "engine_rpm": 1680.0,
  "engine_load_pct": 62.0,
  "machine_speed_kmh": 32.5,
  "fuel_used_l": 45.2,
  "idling_time_min": 12.0,
  "load_cycles": 14,
  "operating_state": "HAULING_LOADED",
  "seatbelt_status": "FASTENED",
  "proximity_distance_m": 42.0,
  "gps_zone": "HAUL_ROAD_NORTH",
  "working_condition": "NORMAL",
  "coolant_temp_c": 86.4,
  "hydraulic_oil_temp_c": 72.1,
  "fault_code": "NONE",
  "task_id": "TSK-DEMO-01"
}
```

### Server Ingestion Acknowledgement (`edge` -> `simulator`)
```json
{
  "status": "ok",
  "machine_id": "CAT-797F-101",
  "timestamp": "2026-09-23T18:15:30Z",
  "broadcast_count": 2,
  "is_new": true
}
```

### Frontend Broadcast Frame (`edge` -> `frontend consoles`)
```json
{
  "type": "telemetry_update",
  "data": {
    "timestamp": "2026-09-23T18:15:30Z",
    "machine_id": "CAT-797F-101",
    "operator_id": "OP-101",
    "engine_hours": 8430.04,
    "engine_rpm": 1680.0,
    "engine_load_pct": 62.0,
    "machine_speed_kmh": 32.5,
    "fuel_used_l": 45.2,
    "idling_time_min": 12.0,
    "load_cycles": 14,
    "operating_state": "HAULING_LOADED",
    "seatbelt_status": "FASTENED",
    "proximity_distance_m": 42.0,
    "gps_zone": "HAUL_ROAD_NORTH",
    "working_condition": "NORMAL",
    "coolant_temp_c": 86.4,
    "hydraulic_oil_temp_c": 72.1,
    "fault_code": "NONE",
    "task_id": "TSK-DEMO-01"
  }
}
```

---

## 5. Logging Tags

All components emit standardized log tags for tracing:
- `[SIMULATOR]` : Transmissions, connects, reconnects, server acknowledgements.
- `[EDGE INGESTION]` : Ingestion frames received from simulator connections.
- `[TELEMETRY VALIDATION]` : Pydantic boundary and schema validation results.
- `[TELEMETRY STORAGE]` : SQLite database persistence and duplicate detection.
- `[WEBSOCKET BROADCAST]` : Fan-out broadcasts to connected frontend cockpits.
