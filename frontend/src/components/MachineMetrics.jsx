import React from 'react';
import { Gauge, Zap, Fuel, RefreshCw, Clock, Flame, Droplets, FastForward, Radar } from 'lucide-react';
import TelemetryValue from './TelemetryValue';
import Sparkline from './Sparkline';
import { useRealtime } from '../context/RealtimeContext';

/**
 * MachineMetrics
 * Grid of primary machinery operating parameters and physical sensor telemetry.
 * Integrates rolling SVG sparklines (last 30-50 points) for RPM, Load, Speed, and Proximity.
 */
export default function MachineMetrics({ telemetry: propTelemetry }) {
  let contextData = {};
  try {
    contextData = useRealtime();
  } catch (e) {
    // Graceful fallback if rendered outside provider
  }

  const telemetry = propTelemetry || contextData.telemetry || {};
  const history = contextData.telemetryHistory || [];

  // Extract metrics with safe defaults
  const speed = telemetry.machine_speed_kmh !== undefined ? Number(telemetry.machine_speed_kmh) : 0.0;
  const rpm = telemetry.engine_rpm !== undefined ? Number(telemetry.engine_rpm) : 0.0;
  const load = telemetry.engine_load_pct !== undefined ? Number(telemetry.engine_load_pct) : 0.0;
  const fuel = telemetry.fuel_used_l !== undefined ? Number(telemetry.fuel_used_l) : 0.0;
  const idle = telemetry.idling_time_min !== undefined ? Number(telemetry.idling_time_min) : 0.0;
  const cycles = telemetry.load_cycles !== undefined ? Number(telemetry.load_cycles) : 0;
  const coolant = telemetry.coolant_temp_c !== undefined ? Number(telemetry.coolant_temp_c) : 82.0;
  const hydraulic = telemetry.hydraulic_oil_temp_c !== undefined ? Number(telemetry.hydraulic_oil_temp_c) : 68.0;
  const proximity = telemetry.proximity_distance_m !== undefined ? Number(telemetry.proximity_distance_m) : 42.0;
  const state = telemetry.operating_state || 'STOPPED';

  // Extract history series for sparklines
  const speedSeries = history.map((h) => h.speed);
  const rpmSeries = history.map((h) => h.rpm);
  const loadSeries = history.map((h) => h.load);
  const proxSeries = history.map((h) => h.proximity);

  // Semantic status determination
  const speedStatus = speed > 40 ? 'warning' : speed > 0 ? 'normal' : 'inactive';
  const rpmStatus = rpm > 2100 ? 'warning' : rpm > 0 ? 'normal' : 'inactive';
  const loadStatus = load > 90 ? 'warning' : load > 60 ? 'normal' : 'safe';
  const coolantStatus = coolant > 98 ? 'critical' : coolant > 93 ? 'warning' : 'safe';
  const idleStatus = idle > 25 ? 'warning' : 'normal';

  // Load bar color
  const loadBarColor = load > 90 ? 'bg-amber-500' : load > 75 ? 'bg-emerald-400' : 'bg-blue-400';

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-mono font-semibold tracking-wider text-zinc-300 uppercase flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
          MACHINE TELEMETRY CLUSTER & TREND BUFFER ({history.length} SAMPLES)
        </h2>
        <span className="text-[11px] font-mono text-zinc-300">
          OPERATIONAL STATE: <strong className="text-emerald-400 font-mono uppercase">{state}</strong>
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {/* Machine Speed with Sparkline */}
        <div className="glass-panel hud-corner p-3.5 sm:p-4 rounded-sm flex flex-col justify-between border-white/[0.08] relative overflow-hidden">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[11px] font-semibold tracking-wider text-zinc-400 uppercase font-mono">
              MACHINE SPEED
            </span>
            <FastForward className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          </div>
          <div className="flex items-baseline gap-1.5 my-0.5">
            <span className="mono-value font-bold tracking-tight text-3xl sm:text-4xl text-zinc-100">
              {speed.toFixed(1)}
            </span>
            <span className="text-xs font-mono text-zinc-400 font-medium">KM/H</span>
          </div>
          <div className="my-1.5">
            <Sparkline
              data={speedSeries}
              color="#38bdf8"
              height={22}
              minBound={0}
              maxBound={50}
              id="speed"
            />
          </div>
          <div className="text-[10px] font-mono text-zinc-400 flex items-center justify-between">
            <span>{speed > 0 ? 'IN MOTION' : 'STATIONARY'}</span>
            <span className="text-zinc-500 font-mono">0-50 KM/H</span>
          </div>
        </div>

        {/* Engine RPM with Sparkline */}
        <div className="glass-panel hud-corner p-3.5 sm:p-4 rounded-sm flex flex-col justify-between border-white/[0.08] relative overflow-hidden">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[11px] font-semibold tracking-wider text-zinc-400 uppercase font-mono">
              ENGINE RPM
            </span>
            <Gauge className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          </div>
          <div className="flex items-baseline gap-1.5 my-0.5">
            <span className="mono-value font-bold tracking-tight text-3xl sm:text-4xl text-zinc-100">
              {rpm.toFixed(0)}
            </span>
            <span className="text-xs font-mono text-zinc-400 font-medium">RPM</span>
          </div>
          <div className="my-1.5">
            <Sparkline
              data={rpmSeries}
              color={rpm > 2100 ? '#f59e0b' : '#10b981'}
              height={22}
              minBound={0}
              maxBound={2500}
              id="rpm"
            />
          </div>
          <div className="text-[10px] font-mono text-zinc-400 flex items-center justify-between">
            <span>{rpm > 1200 ? 'OPERATIONAL BAND' : rpm > 0 ? 'IDLE BAND' : 'STOPPED'}</span>
            <span className="text-zinc-500">MAX 2400</span>
          </div>
        </div>

        {/* Engine Load with Sparkline and Horizontal Utilization Bar */}
        <div className="glass-panel hud-corner p-3.5 sm:p-4 rounded-sm flex flex-col justify-between border-white/[0.08] relative overflow-hidden">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[11px] font-semibold tracking-wider text-zinc-400 uppercase font-mono">
              ENGINE LOAD
            </span>
            <Zap className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          </div>
          <div className="flex items-baseline gap-1.5 my-0.5">
            <span className={`mono-value font-bold tracking-tight text-3xl sm:text-4xl ${load > 90 ? 'text-amber-400' : 'text-zinc-100'}`}>
              {load.toFixed(1)}
            </span>
            <span className="text-xs font-mono text-zinc-400 font-medium">%</span>
          </div>

          {/* Horizontal Utilization Bar */}
          <div className="w-full bg-zinc-800/80 h-1.5 rounded-full overflow-hidden p-0.2 my-1 border border-white/[0.05]">
            <div
              className={`h-full rounded-full transition-all duration-300 ${loadBarColor}`}
              style={{ width: `${Math.min(100, Math.max(0, load))}%` }}
            />
          </div>

          <div className="my-1">
            <Sparkline
              data={loadSeries}
              color={load > 90 ? '#f59e0b' : '#34d399'}
              height={18}
              minBound={0}
              maxBound={100}
              id="load"
            />
          </div>
          <div className="text-[10px] font-mono text-zinc-400 flex items-center justify-between">
            <span>{load > 85 ? 'HEAVY DEMAND' : 'NOMINAL DUTY'}</span>
            <span className="text-zinc-500">UTILIZATION</span>
          </div>
        </div>

        {/* Proximity Clearance with Sparkline */}
        <div className="glass-panel hud-corner p-3.5 sm:p-4 rounded-sm flex flex-col justify-between border-white/[0.08] relative overflow-hidden">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[11px] font-semibold tracking-wider text-zinc-400 uppercase font-mono">
              PROXIMITY CLEARANCE
            </span>
            <Radar className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          </div>
          <div className="flex items-baseline gap-1.5 my-0.5">
            <span className={`mono-value font-bold tracking-tight text-3xl sm:text-4xl ${
              proximity < 5.0 ? 'text-rose-400' : proximity < 15.0 ? 'text-amber-400' : 'text-zinc-100'
            }`}>
              {proximity.toFixed(1)}
            </span>
            <span className="text-xs font-mono text-zinc-400 font-medium">METERS</span>
          </div>
          <div className="my-1.5">
            <Sparkline
              data={proxSeries}
              color={proximity < 5.0 ? '#ef4444' : proximity < 15.0 ? '#f59e0b' : '#10b981'}
              height={22}
              minBound={0}
              maxBound={50}
              id="proximity"
            />
          </div>
          <div className="text-[10px] font-mono text-zinc-400 flex items-center justify-between">
            <span className={proximity < 5.0 ? 'text-rose-400 font-bold' : proximity < 15.0 ? 'text-amber-400' : 'text-zinc-400'}>
              {proximity < 5.0 ? 'CRITICAL HAZARD' : proximity < 15.0 ? 'CAUTION ZONE' : 'SAFE ZONE'}
            </span>
            <span className="text-zinc-500">RADAR BUS</span>
          </div>
        </div>

        {/* Fuel Consumption */}
        <TelemetryValue
          label="FUEL CONSUMED"
          value={fuel.toFixed(1)}
          unit="L"
          status="normal"
          subtext="ACCUMULATED SHIFT"
          icon={Fuel}
          size="md"
        />

        {/* Load Cycles */}
        <TelemetryValue
          label="LOAD CYCLES"
          value={cycles}
          unit="CYC"
          status="safe"
          subtext="VERIFIED HAUL EXITS"
          icon={RefreshCw}
          size="md"
        />

        {/* Idle Time */}
        <TelemetryValue
          label="IDLE TIME"
          value={idle.toFixed(1)}
          unit="MIN"
          status={idleStatus}
          subtext={idle > 20 ? 'EXCESS IDLE ALERT' : 'WITHIN SHIFT TARGET'}
          icon={Clock}
          size="md"
        />

        {/* Coolant Temperature */}
        <TelemetryValue
          label="COOLANT TEMP"
          value={coolant.toFixed(1)}
          unit="°C"
          status={coolantStatus}
          subtext={coolant > 95 ? 'HIGH THERMAL LOAD' : 'NORMAL (82-95°C)'}
          icon={Flame}
          size="md"
        />

        {/* Hydraulic Temperature */}
        <TelemetryValue
          label="HYDRAULIC TEMP"
          value={hydraulic.toFixed(1)}
          unit="°C"
          status={hydraulic > 85 ? 'warning' : 'safe'}
          subtext="PRESSURE STABLE"
          icon={Droplets}
          size="md"
        />
      </div>
    </section>
  );
}
