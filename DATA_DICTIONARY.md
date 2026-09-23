# ShiftGuard — Synthetic Dataset Data Dictionary

> **DISCLAIMER:**  
> All data described in this dictionary is **100% synthetic** and programmatically generated for demonstration, testing, and development of the ShiftGuard Operator Assistant. It does **NOT** represent actual Caterpillar Inc. production data, machine telemetry, or operational records.

---

## 1. `telemetry_history.csv`
Primary historical time-series dataset capturing continuous sensor and operational metrics across 5 Caterpillar machines over an 8-hour shift at 45-second intervals.

- **Location**: `data/synthetic/telemetry_history.csv`
- **Total Records**: 3,200 rows
- **Total Columns**: 19

| Column Name | Data Type | Physical Units / Format | Allowed / Example Values | Description |
|---|---|---|---|---|
| `timestamp` | String (ISO 8601) | `YYYY-MM-DDTHH:MM:SSZ` | `2026-09-20T06:00:00Z` | Universal UTC sampling timestamp (strictly monotonic per machine). |
| `machine_id` | String | Identifier | `CAT-797F-101`, `CAT-6060-201`, etc. | Unique identifier of the heavy machine. |
| `operator_id` | String | Identifier | `OP-101`, `OP-102`, etc. | Assigned equipment operator ID. |
| `engine_hours` | Float | Hours (hrs) | `8420.50` - `16490.00` | Monotonically accumulating total engine operating hours. |
| `engine_rpm` | Float | Revolutions per minute (RPM)| `0.0` (stopped), `680-740` (idle), `1400-2100` (load) | Engine rotational speed correlating with state and load. |
| `engine_load_pct` | Float | Percentage (%) | `0.0` to `98.0` | Percentage of total rated engine load demanded. |
| `machine_speed_kmh` | Float | km/h | `0.0` to `42.0` | Ground travel speed (0 when stopped/idle, >15 when hauling). |
| `fuel_used_l` | Float | Liters (L) | `>= 0.0` (cumulative) | Monotonically accumulating shift fuel consumption in liters. |
| `idling_time_min` | Float | Minutes (min) | `>= 0.0` (cumulative) | Monotonically accumulating time spent in `IDLE` state. |
| `load_cycles` | Integer | Counter | `>= 0` (non-decreasing) | Cumulative count of completed haul or dig cycles. |
| `operating_state` | String | Categorical Enum | `STOPPED`, `IDLE`, `SPOTTING`, `LOADING`, `HAULING_EMPTY`, `HAULING_LOADED`, `DUMPING`, `EXCAVATING`, `DOZING` | Current operational state of the machine. |
| `seatbelt_status` | String | Categorical Enum | `FASTENED`, `UNFASTENED` | Cab operator seatbelt sensor state (normally FASTENED). |
| `proximity_distance_m`| Float | Meters (m) | `0.0` to `60.0` | Distance to nearest vehicle, wall, or obstacle detected by radar/LiDAR. |
| `gps_zone` | String | Pit Geofence Name | `PIT_FLOOR_BENCH_A`, `HAUL_ROAD_NORTH`, `CRUSHER_FEED_1`, `OVERBURDEN_DUMP_WEST`, etc. | Designated open-pit operational mining zone. |
| `working_condition` | String | Categorical Enum | `NORMAL`, `MODERATE`, `SEVERE`, `MUDDY`, `STEEP_INCLINE` | Ground and environmental difficulty condition. |
| `coolant_temp_c` | Float | Degrees Celsius (°C) | `75.0` to `102.0` | Engine coolant temperature with realistic thermal inertia. |
| `hydraulic_oil_temp_c`| Float | Degrees Celsius (°C) | `60.0` to `90.0` | Hydraulic system fluid temperature. |
| `fault_code` | String | Code string | `NONE`, `ENG-TEMP-HIGH-01`, `PRX-WARN-CLOSE-02` | Onboard machine diagnostic trouble code. |
| `task_id` | String | Identifier | `TSK-1001`, `TSK-1002`, etc. | Foreign reference to associated task in `task_history.csv`. |

---

## 2. `task_history.csv`
Dispatched work order assignments and cycle tasks, with realistic causal modeling between weather, operator experience, machine wear, and completion delays.

- **Location**: `data/synthetic/task_history.csv`
- **Total Records**: 150 rows
- **Total Columns**: 12

| Column Name | Data Type | Physical Units / Format | Allowed / Example Values | Description |
|---|---|---|---|---|
| `task_id` | String | Identifier | `TSK-1001` to `TSK-1150` | Unique primary key identifier for the task. |
| `machine_id` | String | Identifier | `CAT-797F-101`, `CAT-D11-401`, etc. | Assigned heavy machinery asset. |
| `operator_id` | String | Identifier | `OP-101` to `OP-105` | Operator dispatched to the task. |
| `task_type` | String | Categorical Enum | `OVERBURDEN_REMOVAL`, `ORE_HAULING`, `BENCH_CLEANUP`, `STOCKPILE_FEEDING`, `RAMP_MAINTENANCE` | Nature of earthmoving operation. |
| `weather` | String | Categorical Enum | `CLEAR`, `DUSTY`, `RAIN`, `MUDDY_GROUND`, `FOG`, `HIGH_WIND` | Ambient weather during the task execution window. |
| `operator_skill` | String | Categorical Enum | `NOVICE`, `INTERMEDIATE`, `EXPERT` | Operator qualification tier affecting productivity. |
| `machine_age_years` | Float | Years (yrs) | `2.1` to `6.5` | Asset operational age influencing cycle efficiency. |
| `estimated_time_min` | Float | Minutes (min) | `40.0` to `110.0` | Planned target completion time. |
| `actual_time_min` | Float | Minutes (min) | `30.0` to `160.0` | Actual observed completion time influenced by skill, weather, and terrain. |
| `planned_start` | String (ISO 8601) | `YYYY-MM-DDTHH:MM:SSZ` | `2026-09-20T06:00:00Z` | Dispatch scheduled start timestamp. |
| `actual_start` | String (ISO 8601) | `YYYY-MM-DDTHH:MM:SSZ` | `2026-09-20T06:04:00Z` | Actual recorded job start time (accounts for staging delay). |
| `working_condition` | String | Categorical Enum | `NORMAL`, `MODERATE`, `SEVERE`, `MUDDY`, `STEEP_INCLINE` | Ground resistance and slope classification. |

---

## 3. `demo_telemetry.csv`
Specialized deterministic time-series sequences crafted for hackathon presentations, judging demonstrations, and integration tests.

- **Location**: `data/synthetic/demo_telemetry.csv`
- **Total Records**: 51 rows
- **Total Columns**: 19 (identical schema to `telemetry_history.csv`)
- **Key Scenarios Encoded**:
  1. **Normal Operation** (Rows 2–9): CAT-797F hauling at 32.5 km/h, normal temps (86.4°C), fastened seatbelt, 42m clear proximity.
  2. **Seatbelt Violation** (Rows 10–16): Moving haul truck at 26.0 km/h with `seatbelt_status == UNFASTENED` and `SEC-SBLT-WARN`.
  3. **Proximity Warning** (Rows 17–22): Distance dropping from 15.2m to 8.2m while spotting near crusher feed (`PRX-WARN-AMBER`).
  4. **Proximity Critical** (Rows 23–28): Obstacle distance collapsing to 2.8m, initiating emergency deceleration to 0 km/h (`PRX-CRIT-STOP`).
  5. **Excessive Idle** (Rows 29–36): CAT-994K idling in staging bay with `idling_time_min` accumulating from 24.5 to 35.0 min (`IDL-EXCESS-WARN`).
  6. **Repeated Safety Behavior** (Rows 37–44): Operator unbuckling while in motion followed by proximity violation within a 2-minute span (`PRX-CRIT-MULTI`, `SEC-SAFETY-STANDDOWN`).
7. **Delayed Task** (Rows 45–52): Haul truck throttled to 6.8 km/h on steep muddy grade with 95.5% engine load and 98.4°C coolant (`TSK-DELAY-TRACTION`).

---

## 4. Phase 6 Anomaly Feature Dataset

The Isolation Forest consumes leakage-free, fixed 15-minute windows derived from telemetry available at or before each window end. These are model features, not raw dataset columns.

| Feature | Definition | Units |
|---|---|---|
| `idle_ratio` | Fraction of samples whose operating state is `IDLE` | 0–1 ratio |
| `fuel_per_load_cycle` | Non-negative fuel counter delta divided by completed-cycle delta (minimum denominator 1) | L/cycle |
| `load_cycles_per_hour` | Completed-cycle delta divided by observed window hours | cycles/hour |
| `fuel_per_active_hour` | Fuel delta divided by observed non-idle/non-stopped hours | L/hour |
| `safety_alert_rate` | Fraction of samples containing seatbelt motion violation, proximity below 15 m, or `SEC-/PRX-` code | 0–1 ratio |
| `seatbelt_violation_rate` | Fraction of samples with unfastened belt while speed exceeds 0.5 km/h | 0–1 ratio |

Counters are differenced only inside the current window. Future samples never affect an earlier window. Missing/non-numeric inputs fail validation rather than being silently imputed.
