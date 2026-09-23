import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import {
  fetchHealth,
  fetchMachines,
  fetchLatestTelemetry,
  fetchTasks,
  fetchSafetyStatus,
  fetchAlerts,
  fetchIncidents,
  fetchIncidentById,
  acknowledgeAlert as apiAcknowledgeAlert,
  acknowledgeIncident as apiAcknowledgeIncident,
  createTelemetryWebSocket,
} from '../services/api';

const RealtimeContext = createContext(null);

const MAX_HISTORY_POINTS = 50;

export function RealtimeProvider({ children }) {
  // Navigation & Machine Scope
  const [selectedMachineId, setSelectedMachineId] = useState('CAT-797F-102');
  const [machines, setMachines] = useState([]);
  const hasManuallySelectedMachine = useRef(false);

  // Core Real-time Telemetry State
  const [telemetry, setTelemetry] = useState(null);
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [lastUpdateTime, setLastUpdateTime] = useState(null);
  const [lastUpdateDate, setLastUpdateDate] = useState(null);
  const [secondsSinceUpdate, setSecondsSinceUpdate] = useState(0);

  // Edge Safety State
  const [safetyState, setSafetyState] = useState({
    overallState: 'NORMAL',
    seatbeltStatus: 'FASTENED',
    proximityDistance: 42.0,
    isCritical: false,
    criticalAlert: null,
    isAcknowledged: false,
  });
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [allAlerts, setAllAlerts] = useState([]);

  // Incidents State
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [loadingIncidentDetail, setLoadingIncidentDetail] = useState(false);
  const [newIncidentToast, setNewIncidentToast] = useState(null);

  // Dispatch Tasks
  const [tasks, setTasks] = useState([]);
  const [currentTask, setCurrentTask] = useState(null);
  const [upcomingTask, setUpcomingTask] = useState(null);

  // System & Connection State
  const [wsConnected, setWsConnected] = useState(false);
  const [edgeConnected, setEdgeConnected] = useState(true);
  const [loadingInitial, setLoadingInitial] = useState(true);

  const wsClientRef = useRef(null);

  // Stale Telemetry Timer (updates secondsSinceUpdate every 1s)
  useEffect(() => {
    const timer = setInterval(() => {
      if (lastUpdateDate) {
        const secs = Math.floor((Date.now() - lastUpdateDate.getTime()) / 1000);
        setSecondsSinceUpdate(secs);
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [lastUpdateDate]);

  // Initial Data Bootstrap
  const loadInitialData = useCallback(async () => {
    try {
      // 1. Health check
      const health = await fetchHealth();
      setEdgeConnected(health.status !== 'offline');

      // 2. Machine fleet
      const fleet = await fetchMachines();
      setMachines(fleet);

      // 3. Telemetry snapshot
      const initialTelem = await fetchLatestTelemetry(selectedMachineId);
      if (initialTelem) {
        setTelemetry(initialTelem);
        setLastUpdateTime(
          initialTelem.timestamp
            ? initialTelem.timestamp.includes('T')
              ? initialTelem.timestamp.slice(11, 19) + ' UTC'
              : initialTelem.timestamp
            : new Date().toTimeString().slice(0, 8) + ' UTC'
        );
        setLastUpdateDate(new Date());
      }

      // 4. Tasks list
      const tasksData = await fetchTasks({ machine_id: selectedMachineId });
      setTasks(tasksData);
      if (tasksData && tasksData.length > 0) {
        setCurrentTask(tasksData[0]);
        setUpcomingTask(tasksData.length > 1 ? tasksData[1] : null);
      }

      // 5. Safety status snapshot
      const safetySnapshot = await fetchSafetyStatus(selectedMachineId);
      if (safetySnapshot) {
        setSafetyState({
          overallState: safetySnapshot.safety_state || 'NORMAL',
          seatbeltStatus: safetySnapshot.seatbelt_status || 'FASTENED',
          proximityDistance: safetySnapshot.proximity_distance_m !== undefined ? safetySnapshot.proximity_distance_m : 42.0,
          isCritical: Boolean(safetySnapshot.is_critical),
          criticalAlert: safetySnapshot.critical_alert || null,
          isAcknowledged: false,
        });
        if (safetySnapshot.active_alerts) {
          setActiveAlerts(safetySnapshot.active_alerts);
        }
      }

      // 6. Alerts & Incidents historical
      const [alertsData, incidentsData] = await Promise.all([
        fetchAlerts({ machine_id: selectedMachineId }),
        fetchIncidents({ machine_id: selectedMachineId }),
      ]);
      setAllAlerts(alertsData);
      setIncidents(incidentsData);
    } catch (err) {
      console.warn('[RealtimeContext] Bootstrap error:', err);
    } finally {
      setLoadingInitial(false);
    }
  }, [selectedMachineId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Process incoming telemetry frame
  const handleIncomingTelemetry = useCallback((frame) => {
    if (!frame) return;

    // Follow simulated machine if not manually fixed
    if (!hasManuallySelectedMachine.current && frame.machine_id && frame.machine_id !== selectedMachineId) {
      setSelectedMachineId(frame.machine_id);
    }

    setTelemetry((prev) => ({ ...(prev || {}), ...frame }));

    const now = new Date();
    setLastUpdateDate(now);
    setSecondsSinceUpdate(0);

    const ts = frame.timestamp
      ? frame.timestamp.includes('T')
        ? frame.timestamp.slice(11, 19) + ' UTC'
        : frame.timestamp
      : now.toTimeString().slice(0, 8) + ' UTC';
    setLastUpdateTime(ts);

    // Update rolling trend sparkline buffers (up to MAX_HISTORY_POINTS)
    setTelemetryHistory((prev) => {
      const next = [
        ...prev,
        {
          timestamp: ts,
          rpm: Number(frame.engine_rpm) || 0,
          load: Number(frame.engine_load_pct) || 0,
          speed: Number(frame.machine_speed_kmh) || 0,
          proximity: Number(frame.proximity_distance_m) || 0,
        },
      ];
      if (next.length > MAX_HISTORY_POINTS) {
        return next.slice(next.length - MAX_HISTORY_POINTS);
      }
      return next;
    });
  }, [selectedMachineId]);

  // Process incoming safety update
  const handleIncomingSafety = useCallback((safetyData) => {
    if (!safetyData) return;

    setSafetyState((prev) => ({
      ...prev,
      overallState: safetyData.safety_state || 'NORMAL',
      seatbeltStatus: safetyData.seatbelt_status || 'FASTENED',
      proximityDistance: safetyData.proximity_distance_m !== undefined ? safetyData.proximity_distance_m : prev.proximityDistance,
      isCritical: Boolean(safetyData.is_critical),
      criticalAlert: safetyData.critical_alert || (safetyData.is_critical ? prev.criticalAlert : null),
      isAcknowledged: safetyData.critical_alert ? safetyData.critical_alert.acknowledged : prev.isAcknowledged,
    }));

    if (safetyData.active_alerts) {
      setActiveAlerts(safetyData.active_alerts);
      setAllAlerts((prev) => {
        const map = new Map(prev.map((a) => [a.id, a]));
        safetyData.active_alerts.forEach((a) => map.set(a.id, a));
        return Array.from(map.values());
      });
    }
  }, []);

  // Process newly declared incident
  const handleIncidentCreated = useCallback((incident) => {
    if (!incident) return;

    setIncidents((prev) => [incident, ...prev.filter((i) => i.id !== incident.id)]);
    // Trigger notification toast
    setNewIncidentToast(incident);
  }, []);

  // Establish Single Persistent WebSocket Connection
  useEffect(() => {
    const wsClient = createTelemetryWebSocket(
      (msg) => {
        if (!msg) return;

        // 1. Initial connection snapshot
        if (msg.type === 'telemetry_initial') {
          if (msg.data) handleIncomingTelemetry(msg.data);
          if (msg.safety) handleIncomingSafety(msg.safety);
        }

        // 2. Live telemetry frame
        if (msg.type === 'telemetry_update' && msg.data) {
          handleIncomingTelemetry(msg.data);
        }

        // 3. Safety update frame
        if (msg.type === 'safety_update' && msg.data) {
          handleIncomingSafety(msg.data);
        }

        // 4. Incident created notification
        if (msg.type === 'incident_created' && msg.data) {
          handleIncidentCreated(msg.data);
        }

        // 5. Alert acknowledged
        if (msg.type === 'alert_acknowledged' && msg.data) {
          const alertId = msg.data.id;
          setActiveAlerts((prev) =>
            prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true, status: 'ACKNOWLEDGED' } : a))
          );
          setSafetyState((prev) => {
            if (prev.criticalAlert && prev.criticalAlert.id === alertId) {
              return { ...prev, isCritical: false, isAcknowledged: true };
            }
            return prev;
          });
        }

        // 6. Incident acknowledged
        if (msg.type === 'incident_acknowledged' && msg.data) {
          const incId = msg.data.id;
          setIncidents((prev) =>
            prev.map((i) => (i.id === incId ? { ...i, status: 'ACKNOWLEDGED' } : i))
          );
        }
      },
      (status) => {
        setWsConnected(Boolean(status?.connected));
      }
    );

    wsClientRef.current = wsClient;

    return () => {
      wsClient.close();
      wsClientRef.current = null;
    };
  }, [handleIncomingTelemetry, handleIncomingSafety, handleIncidentCreated]);

  // Operator Actions
  const selectMachine = (machineId) => {
    hasManuallySelectedMachine.current = true;
    setSelectedMachineId(machineId);
    setTelemetryHistory([]);
  };

  const acknowledgeAlert = async (alertId) => {
    // 1. Send via WebSocket if open
    if (wsClientRef.current) {
      wsClientRef.current.send({
        type: 'acknowledge_alert',
        alert_id: alertId,
        operator_id: 'OP-101',
      });
    }
    // 2. Also call REST endpoint
    try {
      await apiAcknowledgeAlert(alertId, 'OP-101');
    } catch (err) {
      console.warn('[RealtimeContext] REST acknowledge alert failed:', err);
    }

    // Immediate optimistic local update
    setActiveAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true, status: 'ACKNOWLEDGED' } : a))
    );
    setSafetyState((prev) => {
      if (prev.criticalAlert && prev.criticalAlert.id === alertId) {
        return { ...prev, isCritical: false, isAcknowledged: true };
      }
      return prev;
    });
  };

  const acknowledgeIncident = async (incidentId) => {
    if (wsClientRef.current) {
      wsClientRef.current.send({
        type: 'acknowledge_incident',
        incident_id: incidentId,
        operator_id: 'OP-101',
      });
    }
    try {
      await apiAcknowledgeIncident(incidentId, 'OP-101');
    } catch (err) {
      console.warn('[RealtimeContext] REST acknowledge incident failed:', err);
    }
    setIncidents((prev) =>
      prev.map((i) => (i.id === incidentId ? { ...i, status: 'ACKNOWLEDGED' } : i))
    );
    if (selectedIncident && selectedIncident.id === incidentId) {
      setSelectedIncident((prev) => ({ ...prev, status: 'ACKNOWLEDGED' }));
    }
  };

  const openIncidentDetail = async (incidentId) => {
    setLoadingIncidentDetail(true);
    try {
      const detail = await fetchIncidentById(incidentId);
      setSelectedIncident(detail);
    } catch (err) {
      console.warn('[RealtimeContext] Failed to load incident detail:', err);
    } finally {
      setLoadingIncidentDetail(false);
    }
  };

  const closeIncidentDetail = () => {
    setSelectedIncident(null);
  };

  const dismissIncidentToast = () => {
    setNewIncidentToast(null);
  };

  const value = {
    // Machine & Connection
    selectedMachineId,
    selectMachine,
    machines,
    wsConnected,
    edgeConnected,
    loadingInitial,
    lastUpdateTime,
    secondsSinceUpdate,
    isStale: !wsConnected || secondsSinceUpdate > 8,

    // Real-time Telemetry
    telemetry,
    telemetryHistory,

    // Safety Engine
    safetyState,
    activeAlerts,
    allAlerts,
    acknowledgeAlert,

    // Incidents
    incidents,
    selectedIncident,
    loadingIncidentDetail,
    openIncidentDetail,
    closeIncidentDetail,
    acknowledgeIncident,
    newIncidentToast,
    dismissIncidentToast,

    // Tasks
    tasks,
    currentTask,
    upcomingTask,
    refreshData: loadInitialData,
  };

  return (
    <RealtimeContext.Provider value={value}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const ctx = useContext(RealtimeContext);
  if (!ctx) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return ctx;
}
