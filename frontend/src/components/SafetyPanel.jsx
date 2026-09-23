import React from 'react';
import { ShieldCheck, ShieldAlert, Radar, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useRealtime } from '../context/RealtimeContext';

/**
 * SafetyPanel
 * High-visibility authoritative safety status monitor displaying seatbelt interlocks,
 * proximity radar, and active edge safety alerts.
 * 
 * Single source of truth: backend EdgeSafetyEngine via RealtimeContext.
 */
export default function SafetyPanel({ telemetry: propTelemetry }) {
  let contextData = {};
  try {
    contextData = useRealtime();
  } catch (e) {
    // Graceful fallback
  }

  const telemetry = propTelemetry || contextData.telemetry || {};
  const safetyState = contextData.safetyState || {
    overallState: 'NORMAL',
    seatbeltStatus: telemetry.seatbelt_status || 'FASTENED',
    proximityDistance: telemetry.proximity_distance_m !== undefined ? telemetry.proximity_distance_m : 42.0,
    isCritical: false,
    criticalAlert: null,
  };
  const activeAlerts = contextData.activeAlerts || [];

  const seatbelt = safetyState.seatbeltStatus || telemetry.seatbelt_status || 'FASTENED';
  const isSeatbeltFastened = seatbelt === 'FASTENED';

  const proximity = safetyState.proximityDistance !== undefined 
    ? Number(safetyState.proximityDistance) 
    : (telemetry.proximity_distance_m !== undefined ? Number(telemetry.proximity_distance_m) : 42.0);

  // Authoritative status badge
  const overall = safetyState.overallState || 'NORMAL';
  const isCritical = overall === 'CRITICAL';
  const isWarning = overall === 'WARNING';

  // Proximity zone categorization matching EdgeSafetyEngine thresholds
  let proximityLabel = 'SAFE SEPARATION';
  let proximityBarColor = 'bg-emerald-500';
  let proximityBorder = 'border-emerald-500/30';

  if (proximity < 5.0) {
    proximityLabel = 'CRITICAL PROXIMITY (<5.0m)';
    proximityBarColor = 'bg-rose-500';
    proximityBorder = 'border-rose-500/50 shadow-[0_0_20px_rgba(239,68,68,0.25)]';
  } else if (proximity < 15.0) {
    proximityLabel = 'CAUTION PROXIMITY (<15.0m)';
    proximityBarColor = 'bg-amber-500';
    proximityBorder = 'border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.2)]';
  }

  // Calculate percentage fill for proximity bar (clamped 0 to 50 meters)
  const proximityPct = Math.min(100, Math.max(5, (proximity / 50.0) * 100));

  const fault = telemetry.fault_code && telemetry.fault_code !== 'NONE' ? telemetry.fault_code : null;

  return (
    <div className={`glass-panel hud-corner p-5 rounded-sm space-y-4 transition-all duration-300 ${
      isCritical ? 'border-rose-500/50 shadow-[0_0_25px_rgba(239,68,68,0.2)]' : isWarning ? 'border-amber-500/40' : ''
    }`}>
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-2">
          <h2 className="text-xs font-mono font-semibold tracking-wider text-zinc-300 uppercase flex items-center gap-2">
            {isCritical ? (
              <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />
            ) : isWarning ? (
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            ) : (
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            )}
            EDGE SAFETY MONITOR
          </h2>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded-xs font-bold uppercase tracking-wider ${
            isCritical
              ? 'bg-rose-950/80 border border-rose-500/60 text-rose-300 animate-pulse'
              : isWarning
              ? 'bg-amber-950/80 border border-amber-500/50 text-amber-300'
              : 'bg-emerald-950/60 border border-emerald-500/30 text-emerald-300'
          }`}>
            {overall}
          </span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-xs bg-zinc-800/80 text-zinc-300 border border-white/[0.06]">
          AUTHORITATIVE EDGE RULES
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Seatbelt Status Module */}
        <div
          className={`p-4 rounded-xs border transition-all ${
            isSeatbeltFastened
              ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-950/40 border-rose-500/50 text-rose-300 animate-pulse'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-300">
              SEATBELT INTERLOCK
            </span>
            {isSeatbeltFastened ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            )}
          </div>
          <div className="mono-value text-2xl font-bold tracking-tight">
            {seatbelt}
          </div>
          <p className="text-[11px] font-mono mt-1 text-zinc-300">
            {isSeatbeltFastened
              ? 'Interlock secured. Cab operator safely latched.'
              : 'INTERLOCK VIOLATION: Fasten seatbelt immediately.'}
          </p>
        </div>

        {/* Proximity Distance Module */}
        <div className={`p-4 rounded-xs border transition-all ${proximityBorder} bg-[#141720]`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-300">
              PROXIMITY CLEARANCE
            </span>
            <Radar className={`w-4 h-4 ${
              proximity < 5.0 ? 'text-rose-400 animate-spin' : proximity < 15.0 ? 'text-amber-400' : 'text-emerald-400'
            }`} />
          </div>

          <div className="flex items-baseline gap-2">
            <span className="mono-value text-3xl font-bold text-white tracking-tight">
              {proximity.toFixed(1)}
            </span>
            <span className="text-xs font-mono text-zinc-300 font-semibold">METERS</span>
          </div>

          {/* Visual radar distance meter */}
          <div className="mt-2.5">
            <div className="w-full h-2 rounded-xs bg-zinc-800/80 overflow-hidden p-0.5 border border-white/[0.05]">
              <div
                className={`h-full rounded-xs transition-all duration-300 ${proximityBarColor}`}
                style={{ width: `${proximityPct}%` }}
              />
            </div>
            <div className="flex justify-between items-center text-[10px] font-mono text-zinc-300 mt-1">
              <span>0m</span>
              <span className="font-semibold text-zinc-200">{proximityLabel}</span>
              <span>50m+</span>
            </div>
          </div>
        </div>
      </div>

      {/* Active Alerts Strip or Diagnostic Status */}
      {activeAlerts.length > 0 ? (
        <div className="space-y-1.5 pt-1">
          {activeAlerts.slice(0, 2).map((alert) => (
            <div
              key={alert.id}
              className={`flex items-center justify-between p-2.5 rounded-xs border text-xs font-mono ${
                alert.severity === 'CRITICAL'
                  ? 'bg-rose-950/60 border-rose-500/50 text-rose-200'
                  : 'bg-amber-950/40 border-amber-500/40 text-amber-200'
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                <span className="font-semibold shrink-0">[{alert.rule_name || alert.alert_type}]</span>
                <span className="truncate">{alert.message}</span>
              </div>
              <span className="text-[10px] uppercase font-bold shrink-0 ml-2">
                {alert.severity}
              </span>
            </div>
          ))}
        </div>
      ) : fault ? (
        <div className="flex items-center gap-2 p-2.5 rounded-xs bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs font-mono">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
          <span>DIAGNOSTIC ADVISORY: <strong>{fault}</strong></span>
        </div>
      ) : (
        <div className="flex items-center justify-between text-[11px] font-mono text-zinc-300 px-1 pt-1">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>DIAGNOSTIC FAULT CODES:</span>
          </div>
          <span className="text-emerald-400 font-semibold">ZERO ACTIVE ALERTS (SYSTEM OPTIMAL)</span>
        </div>
      )}
    </div>
  );
}
