import React from 'react';
import { AlertTriangle, ArrowRight, GraduationCap } from 'lucide-react';

/**
 * CoachingMoment
 * Compact dashboard widget displaying active coaching recommendations
 * directly on the Command Center cockpit without cluttering operations.
 */
export default function CoachingMoment({
  recommendation,
  onStartTraining,
}) {
  if (!recommendation) return null;

  return (
    <div className="glass-panel p-4 rounded-xs border border-amber-500/40 bg-gradient-to-r from-amber-950/30 via-[#13161f] to-[#12151d] flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-[0_0_15px_rgba(245,158,11,0.08)]">
      <div className="flex items-start gap-3 min-w-0">
        <div className="w-8 h-8 rounded-xs bg-amber-500/15 border border-amber-500/40 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
          <GraduationCap className="w-4 h-4" />
        </div>
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-amber-400">
              COACHING MOMENT
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded-xs bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {recommendation.priority || 'HIGH'} PRIORITY
            </span>
          </div>
          <h4 className="text-sm font-semibold text-white truncate">
            {recommendation.title}
          </h4>
          <p className="text-xs font-mono text-zinc-300 line-clamp-1">
            {recommendation.reason}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => onStartTraining?.(recommendation.lesson_id)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xs bg-amber-500 hover:bg-amber-400 text-zinc-950 font-mono font-bold text-xs uppercase tracking-wider transition-colors shadow-[0_0_12px_rgba(245,158,11,0.3)] cursor-pointer"
        >
          <span>START TRAINING</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
