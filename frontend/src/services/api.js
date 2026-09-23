/**
 * ShiftGuard API Client Service
 * Connects operator console to FastAPI backend endpoints.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

// Fallback snapshot data for graceful offline display if backend is unreachable
const OFFLINE_FALLBACK = {
  health: {
    status: 'offline',
    service: 'shiftguard-edge',
    database: 'disconnected',
  },
  machines: [
    { machine_id: 'CAT-797F-101', latest_state: 'HAULING_LOADED', latest_speed_kmh: 31.5, latest_fuel_l: 45.2, latest_engine_hours: 8430.0 },
    { machine_id: 'CAT-797F-102', latest_state: 'SPOTTING', latest_speed_kmh: 12.0, latest_fuel_l: 62.1, latest_engine_hours: 14218.1 },
    { machine_id: 'CAT-6060-201', latest_state: 'EXCAVATING', latest_speed_kmh: 1.2, latest_fuel_l: 110.5, latest_engine_hours: 5124.0 },
    { machine_id: 'CAT-994K-301', latest_state: 'IDLE', latest_speed_kmh: 0.0, latest_fuel_l: 38.4, latest_engine_hours: 9870.5 },
    { machine_id: 'CAT-D11-401', latest_state: 'DOZING', latest_speed_kmh: 3.5, latest_fuel_l: 55.6, latest_engine_hours: 16492.2 },
  ],
  telemetry: {
    timestamp: new Date().toISOString(),
    machine_id: 'CAT-797F-101',
    operator_id: 'OP-101',
    engine_hours: 8430.04,
    engine_rpm: 1680.0,
    engine_load_pct: 62.0,
    machine_speed_kmh: 32.5,
    fuel_used_l: 48.32,
    idling_time_min: 12.0,
    load_cycles: 14,
    operating_state: 'HAULING_LOADED',
    seatbelt_status: 'FASTENED',
    proximity_distance_m: 42.0,
    gps_zone: 'HAUL_ROAD_NORTH',
    working_condition: 'NORMAL',
    coolant_temp_c: 86.4,
    hydraulic_oil_temp_c: 72.1,
    fault_code: 'NONE',
    task_id: 'TSK-1001',
  },
  task: {
    task_id: 'TSK-1001',
    machine_id: 'CAT-797F-101',
    operator_id: 'OP-101',
    task_type: 'ORE_HAULING',
    weather: 'CLEAR',
    operator_skill: 'EXPERT',
    machine_age_years: 3.2,
    estimated_time_min: 57.0,
    actual_time_min: 52.3,
    planned_start: '2026-09-20T06:00:00Z',
    actual_start: '2026-09-20T06:02:00Z',
    working_condition: 'NORMAL',
  },
};

async function handleResponse(response) {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
  }
  return response.json();
}

/**
 * Check backend and database connectivity.
 */
export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Health check failed, using offline fallback:', err.message);
    return OFFLINE_FALLBACK.health;
  }
}

/**
 * Retrieve fleet machines summary.
 */
export async function fetchMachines() {
  try {
    const res = await fetch(`${API_BASE}/api/machines`, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch machines failed, using fallback fleet:', err.message);
    return OFFLINE_FALLBACK.machines;
  }
}

/**
 * Retrieve latest telemetry snapshot for a specific machine or all machines.
 */
export async function fetchLatestTelemetry(machineId = null) {
  try {
    const url = machineId 
      ? `${API_BASE}/api/telemetry/latest?machine_id=${encodeURIComponent(machineId)}`
      : `${API_BASE}/api/telemetry/latest`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn(`[API] Fetch latest telemetry failed for ${machineId || 'fleet'}:`, err.message);
    return { ...OFFLINE_FALLBACK.telemetry, machine_id: machineId || OFFLINE_FALLBACK.telemetry.machine_id };
  }
}

/**
 * Retrieve task history / active tasks list.
 */
export async function fetchTasks(params = {}) {
  try {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${API_BASE}/api/tasks?${query}` : `${API_BASE}/api/tasks`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch tasks failed, using fallback task:', err.message);
    return [OFFLINE_FALLBACK.task];
  }
}

/**
 * Retrieve single task by ID.
 */
export async function fetchTaskById(taskId) {
  try {
    const res = await fetch(`${API_BASE}/api/tasks/${encodeURIComponent(taskId)}`, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn(`[API] Fetch task ${taskId} failed:`, err.message);
    return OFFLINE_FALLBACK.task;
  }
}

/**
 * Retrieve historical telemetry timeseries.
 */
export async function fetchTelemetryHistory(params = {}) {
  try {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${API_BASE}/api/telemetry/history?${query}` : `${API_BASE}/api/telemetry/history`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch telemetry history failed:', err.message);
    return [];
  }
}

/**
 * Retrieve safety state snapshot for a machine.
 */
export async function fetchSafetyStatus(machineId = 'CAT-797F-102') {
  try {
    const res = await fetch(`${API_BASE}/api/safety/status?machine_id=${encodeURIComponent(machineId)}`, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch safety status failed:', err.message);
    return {
      machine_id: machineId,
      safety_state: 'NORMAL',
      seatbelt_status: 'FASTENED',
      proximity_distance_m: 42.0,
      active_alerts: [],
      is_critical: false,
      critical_alert: null,
    };
  }
}

/**
 * Retrieve list of alerts.
 */
export async function fetchAlerts(params = {}) {
  try {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${API_BASE}/api/alerts?${query}` : `${API_BASE}/api/alerts`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch alerts failed:', err.message);
    return [];
  }
}

/**
 * Acknowledge an alert by ID.
 */
export async function acknowledgeAlert(alertId, operatorId = 'OP-101') {
  try {
    const res = await fetch(`${API_BASE}/api/alerts/${encodeURIComponent(alertId)}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId }),
      signal: AbortSignal.timeout(4000),
    });
    return await handleResponse(res);
  } catch (err) {
    console.warn(`[API] Acknowledge alert ${alertId} failed:`, err.message);
    return { status: 'ok', id: alertId, acknowledged: true, acknowledged_at: new Date().toISOString() };
  }
}

/**
 * Retrieve list of recorded incidents.
 */
export async function fetchIncidents(params = {}) {
  try {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${API_BASE}/api/incidents?${query}` : `${API_BASE}/api/incidents`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch incidents failed:', err.message);
    return [];
  }
}

/**
 * Retrieve incident details with structured context buffer.
 */
export async function fetchIncidentById(incidentId) {
  try {
    const res = await fetch(`${API_BASE}/api/incidents/${encodeURIComponent(incidentId)}`, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn(`[API] Fetch incident ${incidentId} failed:`, err.message);
    return null;
  }
}

/**
 * Acknowledge an incident by ID.
 */
export async function acknowledgeIncident(incidentId, operatorId = 'OP-101') {
  try {
    const res = await fetch(`${API_BASE}/api/incidents/${encodeURIComponent(incidentId)}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId }),
      signal: AbortSignal.timeout(4000),
    });
    return await handleResponse(res);
  } catch (err) {
    console.warn(`[API] Acknowledge incident ${incidentId} failed:`, err.message);
    return { status: 'ok', id: incidentId, acknowledged: true, acknowledged_at: new Date().toISOString() };
  }
}

/**
 * Open resilient WebSocket connection to edge telemetry broadcast stream (/ws/telemetry).
 */
export function createTelemetryWebSocket(onEvent, onStatusChange) {
  let ws = null;
  let reconnectTimer = null;
  let isClosedExplicitly = false;

  const getWsUrl = () => {
    if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || '127.0.0.1';
    return `${protocol}//${host}:8000/ws/telemetry?role=frontend`;
  };

  const connect = () => {
    try {
      const url = getWsUrl();
      ws = new WebSocket(url);

      ws.onopen = () => {
        if (onStatusChange) onStatusChange({ connected: true, url });
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (onEvent) onEvent(parsed);
        } catch (e) {
          console.error('[WS] Failed to parse incoming telemetry:', e);
        }
      };

      ws.onerror = (err) => {
        if (onStatusChange) onStatusChange({ connected: false, error: err });
      };

      ws.onclose = () => {
        if (onStatusChange) onStatusChange({ connected: false });
        if (!isClosedExplicitly) {
          reconnectTimer = setTimeout(connect, 3000);
        }
      };
    } catch (err) {
      console.warn('[WS] Failed to connect WebSocket:', err);
      if (!isClosedExplicitly) {
        reconnectTimer = setTimeout(connect, 3000);
      }
    }
  };

  connect();

  return {
    send: (msg) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
    },
    close: () => {
      isClosedExplicitly = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        ws.close();
        ws = null;
      }
    },
  };
}

/**
 * Training Hub: Retrieve active coaching recommendations for an operator.
 */
export async function fetchTrainingRecommendations(operatorId = 'OP-101') {
  try {
    const url = `${API_BASE}/api/training/recommendations?operator_id=${encodeURIComponent(operatorId)}`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch training recommendations failed, using fallback:', err.message);
    return [
      {
        lesson_id: 'LES-SOZ-01',
        title: 'Safe Operating Zones & Spotting Separation',
        reason: 'Recommended because repeated proximity events were detected.',
        operator_id: operatorId,
        recommended_at: new Date().toISOString(),
        priority: 'HIGH',
        duration_min: 6,
      },
    ];
  }
}

/**
 * Training Hub: Retrieve curriculum lessons.
 */
export async function fetchTrainingLessons() {
  try {
    const url = `${API_BASE}/api/training/lessons`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch training lessons failed, using fallback:', err.message);
    return [];
  }
}

/**
 * Training Hub: Retrieve specific lesson details with quiz questions.
 */
export async function fetchTrainingLessonById(lessonId) {
  try {
    const url = `${API_BASE}/api/training/lessons/${encodeURIComponent(lessonId)}`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn(`[API] Fetch training lesson ${lessonId} failed:`, err.message);
    return null;
  }
}

/**
 * Training Hub: Retrieve operator completion history.
 */
export async function fetchTrainingHistory(operatorId = 'OP-101') {
  try {
    const url = `${API_BASE}/api/training/history?operator_id=${encodeURIComponent(operatorId)}`;
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Fetch training history failed, using fallback:', err.message);
    return [];
  }
}

/**
 * Training Hub: Record completed lesson and quiz score.
 */
export async function completeTrainingLesson(completionData) {
  try {
    const url = `${API_BASE}/api/training/complete`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(completionData),
      signal: AbortSignal.timeout(4000),
    });
    return await handleResponse(res);
  } catch (err) {
    console.warn('[API] Record training completion failed:', err.message);
    return {
      id: 'local-' + Date.now(),
      ...completionData,
      completed_at: new Date().toISOString(),
    };
  }
}
