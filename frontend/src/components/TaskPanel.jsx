import React from 'react';
import { ClipboardList, ArrowRight, Clock, Award, ShieldAlert, Cpu } from 'lucide-react';

/**
 * TaskPanel
 * Details dispatched shift assignments, planned baseline schedule, strict ML ETA notice,
 * and upcoming work orders.
 * 
 * INVARIANT: Predicted ETA is NOT fabricated. Displays MODEL PENDING / ETA MODEL NOT CONNECTED.
 */
export default function TaskPanel({
  currentTask = {},
  upcomingTask = null,
  etaPrediction = null,
}) {
  const plannedTime = currentTask.estimated_time_min !== undefined ? currentTask.estimated_time_min : 55.0;

  return (
    <div className="glass-panel hud-corner p-5 rounded-sm space-y-4">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
        <h2 className="text-xs font-mono font-semibold tracking-wider text-zinc-300 uppercase flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-emerald-400" />
          WORK ORDER DISPATCH & ASSIGNMENT
        </h2>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-xs bg-zinc-800/80 text-zinc-300 border border-white/[0.06]">
          STAGE TRACKER
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Planned Time */}
        <div className="bg-[#141720] border border-white/[0.07] p-3.5 rounded-xs">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-300 block mb-1">
            PLANNED BASELINE
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="mono-value text-2xl font-bold text-white">
              {plannedTime}
            </span>
            <span className="text-xs font-mono text-zinc-300">MIN</span>
          </div>
          <span className="text-[10px] font-mono text-zinc-400 mt-1 block">
            Shift schedule baseline
          </span>
        </div>

        {/* Predicted ML Completion Time - Strict Zero-Fabrication Invariant */}
        <div className="bg-[#141720] border border-amber-500/20 p-3.5 rounded-xs">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-300 block mb-1">
            PREDICTED COMPLETION
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className={`mono-value text-sm sm:text-base font-bold ${etaPrediction ? 'text-emerald-300' : 'text-amber-300'}`}>
              {etaPrediction ? `${etaPrediction.predicted_minutes} MIN` : 'PREDICTION UNAVAILABLE'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-zinc-400 mt-1 block leading-tight">
              {etaPrediction ? `${etaPrediction.delta_vs_plan_minutes >= 0 ? '+' : ''}${etaPrediction.delta_vs_plan_minutes}m vs plan${etaPrediction.why_changed?.length ? ` · ${etaPrediction.why_changed[0]}` : ''}` : 'ETA model not connected'}
          </span>
        </div>

        {/* Operator Skill Profile */}
        <div className="bg-[#141720] border border-white/[0.07] p-3.5 rounded-xs">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-300 block mb-1">
            OPERATOR QUAL
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="mono-value text-lg font-bold text-emerald-300 uppercase">
              {currentTask.operator_skill || 'EXPERT'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-zinc-400 mt-1 block">
            {currentTask.machine_age_years ? `Unit Age: ${currentTask.machine_age_years} yrs` : 'CAT Certified Fleet'}
          </span>
        </div>
      </div>

      {/* Next Queued Task */}
      <div className="p-3 bg-[#11141c] border border-white/[0.06] rounded-xs flex items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2 text-zinc-300 min-w-0">
          <ArrowRight className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <span className="text-zinc-400 shrink-0">NEXT QUEUED:</span>
          <span className="text-zinc-200 font-semibold truncate">
            {upcomingTask
              ? `${upcomingTask.task_id} - ${upcomingTask.task_type.replace(/_/g, ' ')}`
              : 'TSK-1002 - OVERBURDEN EXPEDITION'}
          </span>
        </div>
        <span className="text-[10px] text-zinc-400 shrink-0">AUTO-DISPATCH</span>
      </div>
    </div>
  );
}
