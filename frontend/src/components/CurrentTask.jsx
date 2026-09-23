import React from 'react';
import { Target, Timer, Compass, CloudRain, Mountain, ShieldAlert } from 'lucide-react';

/**
 * CurrentTask
 * Hero operation display presenting the active assignment, ML ETA status, and direct operating state.
 * 
 * INVARIANT: Predicted ETA is NOT fabricated. Displays MODEL PENDING / ETA MODEL NOT CONNECTED
 * until Phase 7 ETA model integration.
 * Operating State is authoritative from backend telemetry (IDLE, WORKING, TRAVELLING, STOPPED).
 */
export default function CurrentTask({
  task = {},
  telemetry = {},
}) {
  const taskName = task.task_type
    ? task.task_type.replace(/_/g, ' ')
    : 'ORE HAULING & DUMP';
  const taskId = task.task_id || telemetry.task_id || 'TSK-1001';

  // Planned baseline duration from dispatch order
  const plannedMin = task.estimated_time_min !== undefined ? task.estimated_time_min : 55.0;

  // Authoritative Operating State from backend telemetry (no React guessing)
  const operatingState = (telemetry.operating_state || 'STOPPED').toUpperCase();

  // Load cycles directly from telemetry
  const cycleCount = telemetry.load_cycles !== undefined ? telemetry.load_cycles : 0;

  return (
    <div className="glass-panel hud-corner p-5 sm:p-6 rounded-sm relative overflow-hidden">
      {/* Background Accent Subtle Glow */}
      <div className="absolute top-0 right-0 w-72 h-72 bg-emerald-500/[0.03] rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
        {/* Left: Task Identity & Environmental Parameters */}
        <div className="space-y-2">
          <div className="flex items-center gap-2.5">
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-mono font-semibold uppercase tracking-wider">
              <Target className="w-3 h-3" />
              ACTIVE MISSION
            </span>
            <span className="text-xs font-mono text-zinc-300">
              DISPATCH ID: <span className="text-zinc-200 font-semibold">{taskId}</span>
            </span>
          </div>

          <h1 className="display-heading text-2xl sm:text-3xl lg:text-4xl font-semibold text-white tracking-tight uppercase">
            {taskName}
          </h1>

          {/* Environmental Badges */}
          <div className="flex flex-wrap items-center gap-3 pt-1 text-xs font-mono text-zinc-300">
            <div className="flex items-center gap-1.5 bg-black/40 px-2.5 py-1 rounded-xs border border-white/[0.05]">
              <Compass className="w-3.5 h-3.5 text-zinc-400" />
              <span>ZONE: <strong className="text-zinc-200">{telemetry.gps_zone || 'HAUL_ROAD_NORTH'}</strong></span>
            </div>
            <div className="flex items-center gap-1.5 bg-black/40 px-2.5 py-1 rounded-xs border border-white/[0.05]">
              <Mountain className="w-3.5 h-3.5 text-zinc-400" />
              <span>TERRAIN: <strong className="text-zinc-200">{telemetry.working_condition || task.working_condition || 'NORMAL'}</strong></span>
            </div>
            {task.weather && (
              <div className="flex items-center gap-1.5 bg-black/40 px-2.5 py-1 rounded-xs border border-white/[0.05]">
                <CloudRain className="w-3.5 h-3.5 text-zinc-400" />
                <span>WEATHER: <strong className="text-zinc-200">{task.weather}</strong></span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Authoritative Operating State & Strict ML ETA Status */}
        <div className="flex flex-wrap items-center gap-6 sm:gap-8 lg:border-l lg:border-white/[0.08] lg:pl-8">
          {/* Strict ML ETA Notice - Zero Fake Calculations */}
          <div className="space-y-1.5 max-w-xs">
            <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-300 font-medium">
              <Timer className="w-3.5 h-3.5 text-amber-400/90" />
              PREDICTED COMPLETION ETA
            </div>
            <div className="flex items-baseline gap-2">
              <span className="mono-value text-xl sm:text-2xl font-bold tracking-tight px-2.5 py-1 rounded-xs bg-amber-500/10 border border-amber-500/30 text-amber-300">
                MODEL PENDING
              </span>
            </div>
            <p className="text-[10px] font-mono text-zinc-400 leading-tight">
              Baseline planned: <strong className="text-zinc-300">{plannedMin}m</strong>. Predicted completion times require the ETA model pipeline (Phase 7).
            </p>
          </div>

          {/* Current Machine Operating State Box (Authoritative Backend State) */}
          <div className="bg-[#12151d] border border-white/[0.08] p-3.5 rounded-xs space-y-1.5 min-w-[150px]">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-300 block">
              OPERATING STATE
            </span>
            <span className={`inline-block px-2.5 py-1 rounded-xs text-xs font-mono font-bold tracking-wide uppercase ${
              operatingState === 'TRAVELLING' 
                ? 'bg-blue-950/60 border border-blue-500/40 text-blue-300'
                : operatingState === 'WORKING'
                ? 'bg-emerald-950/60 border border-emerald-500/40 text-emerald-300'
                : operatingState === 'IDLE'
                ? 'bg-amber-950/60 border border-amber-500/40 text-amber-300'
                : 'bg-zinc-800 border border-zinc-600 text-zinc-300'
            }`}>
              {operatingState}
            </span>
            <div className="text-[10px] font-mono text-zinc-400 pt-0.5">
              Cycle Counter: <strong className="text-zinc-200">{cycleCount} Completed</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
