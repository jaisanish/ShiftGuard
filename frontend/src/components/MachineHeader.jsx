import React, { useState, useEffect } from 'react';
import { Cpu, ShieldCheck, User, Clock, ChevronDown, Activity } from 'lucide-react';

/**
 * MachineHeader
 * Primary cockpit header displaying brand identity, machine selector, operator ID, and real-time edge status.
 */
export default function MachineHeader({
  machines = [],
  selectedMachineId,
  onSelectMachine,
  operatorId = 'OP-101',
  operatorName = 'OPERATOR 1',
  edgeConnected = true,
  wsConnected = false,
  lastTelemetryTime = null,
  secondsSinceUpdate = 0,
  activeTab = 'cockpit',
  onSelectTab,
  hasCoachingAlert = false,
  activeAlertCount = 0,
}) {
  const [currentTime, setCurrentTime] = useState(new Date().toUTCString().slice(17, 25) + ' UTC');

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toUTCString().slice(17, 25) + ' UTC');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="glass-panel border-b border-white/[0.08] px-4 py-3 sm:px-6 sm:py-3.5 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & System Identity */}
      <div className="flex items-center gap-3.5">
        <div className="flex items-center justify-center w-8 h-8 rounded-xs bg-emerald-500/10 border border-emerald-500/40 text-emerald-400">
          <Activity className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="display-heading text-lg font-bold tracking-wider text-white">
              SHIFTGUARD
            </span>
            <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded-xs bg-amber-500/10 text-amber-300 border border-amber-500/30">
              SIMULATED TELEMETRY
            </span>
          </div>
          <p className="text-[10px] font-mono text-zinc-300 tracking-wide">
            CAT SMART OPERATOR ASSISTANT
          </p>
        </div>

        {/* Top-Level Navigation: Command Center | Safety | Incidents | Coach */}
        <div className="hidden sm:flex items-center gap-1 ml-3 pl-3 border-l border-white/[0.08]">
          <button
            onClick={() => onSelectTab?.('cockpit')}
            className={`px-3 py-1.5 rounded-xs text-xs font-mono font-semibold tracking-wider transition-colors cursor-pointer ${
              activeTab === 'cockpit'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.15)]'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]'
            }`}
          >
            COMMAND CENTER
          </button>
          
          <button
            onClick={() => onSelectTab?.('safety')}
            className={`px-3 py-1.5 rounded-xs text-xs font-mono font-semibold tracking-wider transition-colors cursor-pointer relative flex items-center gap-1.5 ${
              activeTab === 'safety'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.15)]'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]'
            }`}
          >
            <span>SAFETY</span>
            {activeAlertCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-red-500/80 text-white font-bold animate-pulse">
                {activeAlertCount}
              </span>
            )}
          </button>

          <button
            onClick={() => onSelectTab?.('incidents')}
            className={`px-3 py-1.5 rounded-xs text-xs font-mono font-semibold tracking-wider transition-colors cursor-pointer ${
              activeTab === 'incidents'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.15)]'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]'
            }`}
          >
            INCIDENTS
          </button>

          <button
            onClick={() => onSelectTab?.('coach')}
            className={`px-3 py-1.5 rounded-xs text-xs font-mono font-semibold tracking-wider transition-colors cursor-pointer relative flex items-center gap-1.5 ${
              activeTab === 'coach'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.15)]'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]'
            }`}
          >
            <span>COACH</span>
            {hasCoachingAlert && (
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            )}
          </button>
        </div>
      </div>

      {/* Machine Selector & Operator Context */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        {/* Machine Selector */}
        <div className="relative">
          <label className="sr-only" htmlFor="machine-select">Select Machine</label>
          <div className="flex items-center gap-2 bg-[#171a22] border border-white/[0.1] px-3 py-1.5 rounded-xs shadow-inner">
            <Cpu className="w-3.5 h-3.5 text-zinc-400" />
            <select
              id="machine-select"
              value={selectedMachineId}
              onChange={(e) => onSelectMachine?.(e.target.value)}
              className="bg-transparent text-xs font-mono font-semibold text-zinc-200 focus:outline-hidden cursor-pointer pr-1"
            >
              {machines.length > 0 ? (
                machines.map((m) => (
                  <option key={m.machine_id} value={m.machine_id} className="bg-zinc-900 text-zinc-200">
                    {m.machine_id} {m.latest_state ? `(${m.latest_state})` : ''}
                  </option>
                ))
              ) : (
                <option value={selectedMachineId} className="bg-zinc-900 text-zinc-200">
                  {selectedMachineId}
                </option>
              )}
            </select>
          </div>
        </div>

        {/* Operator Badge */}
        <div className="flex items-center gap-2 bg-[#171a22] border border-white/[0.1] px-3 py-1.5 rounded-xs">
          <User className="w-3.5 h-3.5 text-emerald-400" />
          <div className="flex items-baseline gap-1.5 text-xs font-mono">
            <span className="font-semibold text-zinc-200">OPERATOR 1</span>
          </div>
        </div>

        {/* Live Cockpit Clock */}
        <div className="hidden lg:flex items-center gap-2 bg-[#171a22] border border-white/[0.08] px-3 py-1.5 rounded-xs text-xs font-mono text-zinc-400">
          <Clock className="w-3.5 h-3.5 text-zinc-500" />
          <span>{currentTime}</span>
        </div>

        {/* Real-time WebSocket Streaming Status & Last Update */}
        <div
          className={`flex flex-col justify-center px-2.5 py-1 rounded-xs border font-mono tracking-wide ${
            wsConnected
              ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
              : 'bg-amber-950/40 border-amber-500/40 text-amber-300'
          }`}
        >
          <div className="flex items-center gap-1.5 text-[11px] font-semibold">
            <span
              className={`w-2 h-2 rounded-full ${
                wsConnected ? 'bg-emerald-400 pulse-active' : 'bg-amber-400 animate-pulse'
              }`}
            />
            <span>{wsConnected ? 'LIVE TELEMETRY ●' : 'TELEMETRY DISCONNECTED'}</span>
          </div>
          <div className="text-[9px] font-normal flex items-center justify-between gap-2 mt-0.5">
            <span className={wsConnected ? 'text-emerald-400' : 'text-amber-400'}>
              {wsConnected ? 'WEBSOCKET: CONNECTED' : 'WEBSOCKET: RECONNECTING...'}
            </span>
            {lastTelemetryTime && (
              <span className="text-zinc-400 hidden sm:inline">
                LAST UPDATE: <strong className="text-zinc-200">{lastTelemetryTime}</strong>
                {!wsConnected && secondsSinceUpdate > 0 && ` (${secondsSinceUpdate}s ago)`}
              </span>
            )}
          </div>
        </div>

        {/* Edge Compute Status Indicator */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-xs border text-xs font-mono tracking-wide ${
            edgeConnected
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.15)]'
              : 'bg-amber-950/40 border-amber-500/30 text-amber-400'
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              edgeConnected ? 'bg-emerald-400 pulse-active' : 'bg-amber-400'
            }`}
          />
          <span className="font-semibold">
            {edgeConnected ? 'EDGE: ACTIVE' : 'EDGE: STANDBY'}
          </span>
        </div>
      </div>
    </header>
  );
}
