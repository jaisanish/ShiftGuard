import React, { useState, useEffect } from 'react';
import { useRealtime } from '../context/RealtimeContext';
import { fetchTrainingRecommendations } from '../services/api';

import MachineHeader from './MachineHeader';
import CurrentTask from './CurrentTask';
import MachineMetrics from './MachineMetrics';
import SafetyPanel from './SafetyPanel';
import TaskPanel from './TaskPanel';
import SystemStatus from './SystemStatus';
import CoachingMoment from './CoachingMoment';
import CopilotEntry from './CopilotEntry';
import CriticalAlertOverlay from './CriticalAlertOverlay';
import IncidentNotificationToast from './IncidentNotificationToast';
import SafetyPage from './SafetyPage';
import IncidentsPage from './IncidentsPage';
import CoachPage from './training/CoachPage';
import AnalyticsPage from './AnalyticsPage';
import AnomalyInsightCard from './AnomalyInsightCard';

import { AlertCircle, RefreshCw, Radio } from 'lucide-react';

/**
 * OperatorConsole
 * Main orchestrator for ShiftGuard CAT Heavy Machinery Realtime Operator Console.
 * Powered by RealtimeContext for low-latency WebSocket streaming & authoritative edge safety.
 */
export default function OperatorConsole() {
  const {
    machines,
    selectedMachineId,
    selectMachine,
    telemetry,
    currentTask,
    upcomingTask,
    wsConnected,
    edgeConnected,
    loadingInitial,
    lastUpdateTime,
    secondsSinceUpdate,
    isStale,
    activeAlerts,
    openIncidentDetail,
    refreshData,
    anomalyInsight,
    anomalyModelHealth,
    etaPrediction,
    etaModelHealth,
  } = useRealtime();

  const [activeTab, setActiveTab] = useState('cockpit'); // cockpit | safety | incidents | insights | coach
  const [coachingRecommendation, setCoachingRecommendation] = useState(null);
  const [targetLessonId, setTargetLessonId] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch coaching recommendations for active operator
  useEffect(() => {
    let isSubscribed = true;
    async function loadCoaching() {
      try {
        const opId = telemetry?.operator_id || 'OP-101';
        const recData = await fetchTrainingRecommendations(opId);
        if (isSubscribed && Array.isArray(recData) && recData.length > 0) {
          setCoachingRecommendation(recData[0]);
        }
      } catch (err) {
        console.warn('[OperatorConsole] Failed to fetch coaching recommendations:', err);
      }
    }
    loadCoaching();
    return () => {
      isSubscribed = false;
    };
  }, [telemetry?.operator_id]);

  const handleManualRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshData();
    } finally {
      setTimeout(() => setRefreshing(false), 500);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#08090c] text-zinc-100 font-sans">
      {/* 1. Critical Alert Modal Overlay (Authoritative Backend CRITICAL Events) */}
      <CriticalAlertOverlay />

      {/* 2. Realtime Incident Notification Toast */}
      <IncidentNotificationToast
        onOpenIncident={(incidentId) => {
          setActiveTab('incidents');
          openIncidentDetail(incidentId);
        }}
      />

      {/* 3. Cockpit Header & Navigation */}
      <MachineHeader
        machines={machines}
        selectedMachineId={selectedMachineId}
        onSelectMachine={selectMachine}
        operatorId={telemetry?.operator_id || 'OP-101'}
        operatorName="OPERATOR 1"
        edgeConnected={edgeConnected}
        wsConnected={wsConnected}
        lastTelemetryTime={lastUpdateTime}
        secondsSinceUpdate={secondsSinceUpdate}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        hasCoachingAlert={Boolean(coachingRecommendation)}
        activeAlertCount={activeAlerts.length}
      />

      {/* Main Cockpit Display Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-5 sm:px-6 sm:py-6 space-y-5">
        {/* Offline / Cache Banner Notice */}
        {!edgeConnected && (
          <div className="flex items-center justify-between p-3 rounded-xs bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs font-mono">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                EDGE BACKEND SERVICE UNREACHABLE — OPERATING IN AIR-GAPPED STANDALONE MODE
              </span>
            </div>
            <button
              onClick={handleManualRefresh}
              className="px-2.5 py-1 rounded-xs bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/30 transition-colors cursor-pointer"
            >
              RECONNECT
            </button>
          </div>
        )}

        {/* Dynamic Route: Tab Pages */}
        {activeTab === 'safety' ? (
          <SafetyPage />
        ) : activeTab === 'incidents' ? (
          <IncidentsPage />
        ) : activeTab === 'coach' ? (
          <CoachPage
            operatorId={telemetry?.operator_id || 'OP-101'}
            initialLessonId={targetLessonId}
            onReturnToCockpit={() => {
              setTargetLessonId(null);
              setActiveTab('cockpit');
            }}
          />
        ) : activeTab === 'insights' ? (
          <AnalyticsPage />
        ) : loadingInitial ? (
          <div className="glass-panel p-16 rounded-sm text-center space-y-4">
            <Radio className="w-8 h-8 text-emerald-400 animate-pulse mx-auto" />
            <div className="display-heading text-lg text-zinc-200 font-semibold tracking-wide">
              INITIALIZING CAT COCKPIT BUS...
            </div>
            <p className="text-xs font-mono text-zinc-400">
              Connecting to ShiftGuard Edge Node & WebSocket stream
            </p>
          </div>
        ) : (
          <>
            {/* Stale Telemetry Warning Banner (if no updates received for >8s) */}
            {isStale && wsConnected && (
              <div className="flex items-center justify-between px-3 py-2 rounded-xs bg-amber-950/30 border border-amber-500/30 text-amber-300 text-xs font-mono">
                <span>SIMULATOR TELEMETRY PAUSED (Last update {secondsSinceUpdate}s ago)</span>
                <span className="text-[10px] text-zinc-400">Run simulator scenario to resume stream</span>
              </div>
            )}

            {/* Compact Coaching Moment Card (when active recommendation exists) */}
            {coachingRecommendation && (
              <CoachingMoment
                recommendation={coachingRecommendation}
                onStartTraining={(lessonId) => {
                  setTargetLessonId(lessonId);
                  setActiveTab('coach');
                }}
              />
            )}

            <AnomalyInsightCard
              insight={anomalyInsight}
              modelHealth={anomalyModelHealth}
              onOpenInsights={() => setActiveTab('insights')}
            />

            {/* Ask ShiftGuard In-Cab Entry */}
            <CopilotEntry />

            {/* Current Operation Hero Area */}
            <CurrentTask
              task={currentTask || {}}
              telemetry={telemetry || {}}
              etaPrediction={etaPrediction}
              etaModelHealth={etaModelHealth}
            />

            {/* Primary Machinery Telemetry Metric Cluster & Trend Sparklines */}
            <MachineMetrics
              telemetry={telemetry || {}}
            />

            {/* Split Deck: Safety Panel (Left) & Task Panel (Right) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <SafetyPanel
                telemetry={telemetry || {}}
              />
              <TaskPanel
                currentTask={currentTask || {}}
                upcomingTask={upcomingTask}
                etaPrediction={etaPrediction}
                etaModelHealth={etaModelHealth}
              />
            </div>

            {/* Co-Pilot Services & Edge Node Integrity */}
            <SystemStatus
              edgeConnected={edgeConnected}
            />
          </>
        )}
      </main>

      {/* Cockpit Footer Status Bar */}
      <footer className="glass-panel border-t border-white/[0.06] px-4 py-2.5 sm:px-6 flex flex-wrap items-center justify-between text-[11px] font-mono text-zinc-400 gap-3 mt-auto">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            CAN-BUS 2.0B / J1939 LINK STABLE
          </span>
          <span className="hidden sm:inline text-zinc-600">|</span>
          <span className="hidden sm:inline">
            SQLITE NODE: <strong className="text-zinc-300">CONNECTED</strong>
          </span>
          <span className="hidden sm:inline text-zinc-600">|</span>
          <span className="text-zinc-400">
            ENGINE: <strong className="text-emerald-400 font-bold">EDGE LOCAL</strong>
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-xs bg-zinc-800/80 hover:bg-zinc-700/80 text-zinc-300 transition-colors border border-white/[0.05] cursor-pointer disabled:opacity-50"
            title="Refresh telemetry snapshot from backend"
          >
            <RefreshCw className={`w-3 h-3 ${refreshing ? 'animate-spin text-emerald-400' : ''}`} />
            <span>{refreshing ? 'SYNCING...' : 'POLL TELEMETRY'}</span>
          </button>
          <span className="text-zinc-500">ShiftGuard v2.0-EDGE</span>
        </div>
      </footer>
    </div>
  );
}
