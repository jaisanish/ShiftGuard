import React from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Radar,
  CheckCircle2,
  Clock,
  Activity,
  Compass,
  Mountain,
} from 'lucide-react';
import { useRealtime } from '../context/RealtimeContext';

/**
 * SafetyPage
 * Dedicated In-Cab Edge Safety screen.
 * Visually communicates deterministic edge safety, active and recent alerts,
 * seatbelt interlocks, and live obstacle radar metrics.
 */
export default function SafetyPage() {
  const {
    telemetry,
    safetyState,
    activeAlerts,
    allAlerts,
    acknowledgeAlert,
    currentTask,
  } = useRealtime();

  const overall = safetyState.overallState || 'NORMAL';
  const seatbelt = telemetry?.seatbelt_status || safetyState.seatbeltStatus || 'FASTENED';
  const isSeatbeltFastened = seatbelt === 'FASTENED';
  const proximity = telemetry?.proximity_distance_m !== undefined
    ? Number(telemetry.proximity_distance_m)
    : safetyState.proximityDistance || 42.0;
  const opState = telemetry?.operating_state || 'IDLE';

  // Radar color and bar width
  const proximityPct = Math.min(100, Math.max(4, (proximity / 50.0) * 100));
  let proximityColor = 'bg-emerald-500';
  let proximityText = 'text-emerald-400';
  if (proximity <= 2.0) {
    proximityColor = 'bg-rose-500';
    proximityText = 'text-rose-400';
  } else if (proximity <= 5.0) {
    proximityColor = 'bg-amber-500';
    proximityText = 'text-amber-400';
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* 1. Authoritative Edge Safety Header Banner */}
      <div className="glass-panel p-4 sm:p-5 rounded-sm border border-emerald-500/30 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xs bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-300">
                SOURCE: LOCAL EDGE SAFETY ENGINE
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-xs bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 font-semibold">
                DETERMINISTIC
              </span>
            </div>
            <p className="text-xs text-zinc-300 font-mono mt-0.5">
              Cab safety rules execute locally with 100% determinism. Zero dependency on cloud or probabilistic AI.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="bg-[#141720] border border-white/[0.08] px-3 py-1.5 rounded-xs flex items-center gap-2">
            <span className="text-zinc-400">EDGE ENGINE:</span>
            <strong className="text-emerald-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-active" />
              ONLINE & ENFORCING
            </strong>
          </div>
        </div>
      </div>

      {/* 2. Top Metric Cards: Overall State, Seatbelt, Proximity, Kinematics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        {/* Overall Safety State */}
        <div
          className={`p-4 rounded-xs border transition-all ${
            overall === 'CRITICAL'
              ? 'bg-rose-950/40 border-rose-500/60 shadow-[0_0_20px_rgba(244,63,94,0.25)]'
              : overall === 'WARNING'
              ? 'bg-amber-950/40 border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.2)]'
              : 'bg-emerald-950/30 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.15)]'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-zinc-400 uppercase tracking-wider mb-2">
            <span>OVERALL SAFETY</span>
            {overall === 'CRITICAL' ? (
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            ) : overall === 'WARNING' ? (
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            ) : (
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            )}
          </div>
          <div
            className={`mono-value text-3xl font-black tracking-tight ${
              overall === 'CRITICAL'
                ? 'text-rose-400'
                : overall === 'WARNING'
                ? 'text-amber-400'
                : 'text-emerald-400'
            }`}
          >
            {overall}
          </div>
          <span className="text-[11px] text-zinc-300 block mt-1">
            {overall === 'CRITICAL'
              ? 'Emergency stop / hazard active'
              : overall === 'WARNING'
              ? 'Caution required: boundary breach'
              : 'All safety interlocks nominal'}
          </span>
        </div>

        {/* Seatbelt Compliance */}
        <div
          className={`p-4 rounded-xs border transition-all ${
            isSeatbeltFastened
              ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-950/40 border-rose-500/60 text-rose-300 animate-pulse'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-zinc-400 uppercase tracking-wider mb-2">
            <span>SEATBELT INTERLOCK</span>
            <ShieldCheck className={`w-4 h-4 ${isSeatbeltFastened ? 'text-emerald-400' : 'text-rose-400'}`} />
          </div>
          <div className="mono-value text-2xl font-bold tracking-tight">
            {seatbelt}
          </div>
          <span className="text-[11px] text-zinc-300 block mt-1">
            {isSeatbeltFastened
              ? 'Cab operator buckled & locked'
              : 'UNFASTENED: Motion interlock tripped'}
          </span>
        </div>

        {/* Live Proximity Radar */}
        <div className="bg-[#141720] border border-white/[0.08] p-4 rounded-xs space-y-2">
          <div className="flex items-center justify-between text-xs text-zinc-400 uppercase tracking-wider">
            <span>LIVE PROXIMITY</span>
            <Radar className={`w-4 h-4 ${proximityText}`} />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`mono-value text-3xl font-black ${proximityText}`}>
              {proximity.toFixed(1)}
            </span>
            <span className="text-xs text-zinc-400">METERS</span>
          </div>

          <div className="w-full h-2 rounded-xs bg-zinc-800/80 overflow-hidden border border-white/[0.05]">
            <div
              className={`h-full rounded-xs transition-all duration-300 ${proximityColor}`}
              style={{ width: `${proximityPct}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-zinc-400">
            <span>0m (Crit: 2m)</span>
            <span>Warn: 5m</span>
            <span>50m+</span>
          </div>
        </div>

        {/* Kinematic Operating State */}
        <div className="bg-[#141720] border border-white/[0.08] p-4 rounded-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 uppercase tracking-wider mb-2">
            <span>OPERATING STATE</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mono-value text-2xl font-bold text-white uppercase">
            {opState}
          </div>
          <span className="text-[11px] text-zinc-300 block mt-1">
            Speed: <strong>{telemetry?.machine_speed_kmh?.toFixed(1) || '0.0'} km/h</strong> | RPM: <strong>{telemetry?.engine_rpm?.toFixed(0) || '0'}</strong>
          </span>
        </div>
      </div>

      {/* 3. Current Mission Context Strip */}
      <div className="glass-panel p-4 rounded-sm flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 text-zinc-300">
            <Compass className="w-4 h-4 text-emerald-400" />
            <span>MINE ZONE: <strong className="text-white">{telemetry?.gps_zone || currentTask?.gps_zone || 'HAUL_ROAD_NORTH'}</strong></span>
          </div>
          <div className="flex items-center gap-2 text-zinc-300">
            <Mountain className="w-4 h-4 text-emerald-400" />
            <span>TERRAIN: <strong className="text-white">{telemetry?.working_condition || currentTask?.working_condition || 'NORMAL'}</strong></span>
          </div>
          <div className="flex items-center gap-2 text-zinc-300">
            <span>MISSION ID: <strong className="text-emerald-400">{currentTask?.task_id || telemetry?.task_id || 'TSK-1001'}</strong></span>
          </div>
        </div>
        <span className="text-[11px] text-zinc-400">
          EDGE INGESTION FREQUENCY: 1.0 HZ
        </span>
      </div>

      {/* 4. Active Safety Alerts Section */}
      <div className="glass-panel p-5 rounded-sm space-y-4 font-mono">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase text-zinc-200">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>ACTIVE SAFETY ALERTS ({activeAlerts.length})</span>
          </div>
          <span className="text-[10px] text-zinc-400">
            AUTHORITATIVE EDGE AUDIT LOG
          </span>
        </div>

        {activeAlerts.length === 0 ? (
          <div className="py-8 text-center space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
            <div className="text-sm font-semibold text-zinc-200">
              ZERO ACTIVE SAFETY ALERTS
            </div>
            <p className="text-xs text-zinc-400">
              All deterministic rule constraints (proximity separation, seatbelt interlock, thermal bounds) are nominal.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-xs border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  alert.severity === 'CRITICAL'
                    ? 'bg-rose-950/40 border-rose-500/60 text-rose-100'
                    : 'bg-amber-950/30 border-amber-500/40 text-amber-100'
                }`}
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2 text-xs">
                    <span
                      className={`px-2 py-0.5 rounded-xs font-bold text-[10px] uppercase ${
                        alert.severity === 'CRITICAL'
                          ? 'bg-rose-600 text-white'
                          : 'bg-amber-600 text-black'
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <span className="font-bold text-white">{alert.title}</span>
                    <span className="text-zinc-400">•</span>
                    <span className="text-[11px] text-zinc-300">
                      {alert.timestamp ? alert.timestamp.slice(11, 19) + ' UTC' : 'NOW'}
                    </span>
                    {alert.acknowledged && (
                      <span className="px-1.5 py-0.2 rounded-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px]">
                        ACKNOWLEDGED
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-medium text-zinc-200">
                    {alert.message}
                  </p>
                  {alert.code && alert.code !== 'NONE' && (
                    <span className="text-[10px] text-zinc-400 block">
                      FAULT CODE: <strong>{alert.code}</strong>
                    </span>
                  )}
                </div>

                {!alert.acknowledged && (
                  <button
                    onClick={() => acknowledgeAlert(alert.id)}
                    className="self-start sm:self-center px-3.5 py-2 rounded-xs bg-white/[0.08] hover:bg-white/[0.15] text-xs font-bold tracking-wider uppercase border border-white/[0.2] transition-colors cursor-pointer shrink-0"
                  >
                    ACKNOWLEDGE
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. Historical Alerts Table */}
      <div className="glass-panel p-5 rounded-sm space-y-4 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2 font-semibold uppercase text-zinc-200">
            <Clock className="w-4 h-4 text-zinc-400" />
            <span>RECENT ALERTS LOG</span>
          </div>
          <span className="text-[10px] text-zinc-400">
            STORED IN EDGE SQLITE
          </span>
        </div>

        {allAlerts.length === 0 ? (
          <p className="text-zinc-400 py-4 text-center">No alerts logged in current shift session.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/[0.06] text-zinc-400 text-[11px]">
                  <th className="pb-2">TIME (UTC)</th>
                  <th className="pb-2">TYPE</th>
                  <th className="pb-2">SEVERITY</th>
                  <th className="pb-2">MESSAGE</th>
                  <th className="pb-2">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {allAlerts.slice(0, 10).map((a) => (
                  <tr key={a.id} className="hover:bg-white/[0.02]">
                    <td className="py-2.5 text-zinc-300">{a.timestamp?.slice(11, 19) || '—'}</td>
                    <td className="py-2.5 font-bold text-white">{a.alert_type}</td>
                    <td className="py-2.5">
                      <span
                        className={`px-1.5 py-0.5 rounded-xs text-[10px] font-bold ${
                          a.severity === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}
                      >
                        {a.severity}
                      </span>
                    </td>
                    <td className="py-2.5 text-zinc-300 max-w-xs truncate">{a.message}</td>
                    <td className="py-2.5">
                      <span className={`text-[10px] font-semibold ${
                        a.status === 'RESOLVED' ? 'text-zinc-400' : a.status === 'ACKNOWLEDGED' ? 'text-blue-400' : 'text-amber-400'
                      }`}>
                        {a.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
