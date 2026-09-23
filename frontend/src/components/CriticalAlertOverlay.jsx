import React from 'react';
import { AlertOctagon, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useRealtime } from '../context/RealtimeContext';

/**
 * CriticalAlertOverlay
 * Dominant, high-contrast modal overlay triggered strictly by authoritative
 * backend CRITICAL safety events. Requires operator acknowledgment to dismiss.
 */
export default function CriticalAlertOverlay() {
  const { safetyState, acknowledgeAlert } = useRealtime();

  const isVisible = safetyState.isCritical && safetyState.criticalAlert && !safetyState.isAcknowledged;
  const alert = safetyState.criticalAlert;

  if (!isVisible || !alert) return null;

  const title = alert.title || 'CRITICAL SAFETY HAZARD';
  const message = alert.message || 'Immediate operator intervention required.';
  const alertType = alert.alert_type || 'HAZARD';

  // Extract proximity distance or kinematic evidence if available
  const dist = alert.evidence?.proximity_distance_m !== undefined
    ? Number(alert.evidence.proximity_distance_m).toFixed(1) + ' m'
    : (safetyState.proximityDistance !== undefined ? Number(safetyState.proximityDistance).toFixed(1) + ' m' : null);

  const handleAcknowledge = () => {
    acknowledgeAlert(alert.id);
  };

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="critical-alert-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in"
    >
      {/* Heavy Red Pulsing Glow Effect */}
      <div className="absolute inset-0 pointer-events-none border-8 border-rose-600/70 animate-pulse shadow-[inset_0_0_120px_rgba(225,29,72,0.5)]" />

      {/* Primary Alert Card Container */}
      <div className="relative w-full max-w-xl bg-[#0c0d12] border-2 border-rose-600 rounded-sm shadow-2xl p-6 sm:p-8 space-y-6 text-center z-10 overflow-hidden">
        {/* Diagonal Warning Stripes Accent Header */}
        <div className="absolute top-0 left-0 right-0 h-3 bg-repeating-linear-gradient-[45deg,theme(colors.rose.600),theme(colors.rose.600)_12px,theme(colors.black)_12px,theme(colors.black)_24px]" />

        {/* Alarm Header Badge */}
        <div className="pt-2 flex items-center justify-center gap-2 text-rose-500 font-mono text-xs font-bold tracking-widest uppercase">
          <AlertOctagon className="w-5 h-5 animate-bounce" />
          <span>EDGE SAFETY ENGINE — IMMEDIATE THREAT</span>
        </div>

        {/* Hazard Title & Prominent Metric */}
        <div className="space-y-2">
          <h2
            id="critical-alert-title"
            className="display-heading text-3xl sm:text-4xl font-extrabold text-white tracking-tight uppercase"
          >
            {title}
          </h2>

          {alertType === 'PROXIMITY' && dist && (
            <div className="py-2">
              <div className="mono-value text-6xl sm:text-7xl font-black text-rose-500 tracking-tight drop-shadow-[0_0_35px_rgba(244,63,94,0.6)]">
                {dist}
              </div>
              <span className="text-xs font-mono text-rose-300 font-bold uppercase tracking-wider block mt-1">
                OBSTACLE SEPARATION BREACH
              </span>
            </div>
          )}

          {alertType === 'SEATBELT' && (
            <div className="py-2">
              <div className="mono-value text-4xl sm:text-5xl font-black text-rose-500 tracking-tight">
                UNFASTENED
              </div>
              <span className="text-xs font-mono text-rose-300 font-bold uppercase tracking-wider block mt-1">
                VEHICLE IN MOTION INTERLOCK TRIGGERED
              </span>
            </div>
          )}
        </div>

        {/* Severity Badge & Detailed Message */}
        <div className="bg-rose-950/60 border border-rose-600/60 p-4 rounded-xs text-left space-y-2">
          <div className="flex items-center justify-between">
            <span className="px-2 py-0.5 rounded-xs bg-rose-600 text-white font-mono text-xs font-bold uppercase tracking-wider">
              CRITICAL SEVERITY
            </span>
            <span className="text-[10px] font-mono text-rose-300">
              TIME: {alert.timestamp ? alert.timestamp.slice(11, 19) + ' UTC' : 'NOW'}
            </span>
          </div>
          <p className="text-sm font-mono text-rose-100 font-medium">
            {message}
          </p>
        </div>

        {/* Acknowledge Button */}
        <div className="pt-2">
          <button
            onClick={handleAcknowledge}
            className="w-full py-4 px-6 rounded-xs bg-rose-600 hover:bg-rose-500 active:bg-rose-700 text-white font-mono font-bold text-base tracking-wider uppercase shadow-[0_0_30px_rgba(225,29,72,0.4)] transition-all cursor-pointer flex items-center justify-center gap-3 border border-rose-400"
          >
            <CheckCircle2 className="w-5 h-5" />
            <span>ACKNOWLEDGE HAZARD</span>
          </button>
          <p className="text-[11px] font-mono text-zinc-400 mt-2">
            Operator acknowledgment will be permanently logged to local edge SQLite audit trail.
          </p>
        </div>
      </div>
    </div>
  );
}
