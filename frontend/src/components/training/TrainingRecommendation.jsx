import React from 'react';
import { Award, Clock, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';

/**
 * TrainingRecommendation
 * Hero recommendation card displaying active coaching recommendations
 * derived from operator telemetry and hazard events.
 */
export default function TrainingRecommendation({
  recommendation,
  onStartLesson,
}) {
  if (!recommendation) return null;

  return (
    <div className="glass-panel hud-corner p-5 sm:p-6 rounded-sm relative overflow-hidden border border-amber-500/30 bg-gradient-to-br from-[#12151d] via-[#10131a] to-[#14120a]">
      {/* Background Accent Subtle Glow */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/[0.04] rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
        <div className="space-y-2.5 max-w-2xl">
          <div className="flex items-center gap-2.5">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-xs bg-amber-500/15 border border-amber-500/40 text-amber-300 text-[10px] font-mono font-semibold uppercase tracking-wider">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              RECOMMENDED COACHING
            </span>
            <span className="text-xs font-mono text-zinc-400 flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-zinc-400" />
              {recommendation.duration_min} MIN DURATION
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-xs bg-red-950/40 border border-red-500/30 text-red-300 uppercase">
              {recommendation.priority || 'HIGH'} PRIORITY
            </span>
          </div>

          <h2 className="display-heading text-xl sm:text-2xl font-bold text-white tracking-tight uppercase">
            {recommendation.title}
          </h2>

          <div className="p-3 rounded-xs bg-black/40 border border-white/[0.06] text-xs font-mono text-zinc-300 space-y-1">
            <span className="text-[10px] uppercase tracking-wider text-amber-400/90 font-semibold block">
              TRIGGER RATIONALE
            </span>
            <p className="text-zinc-200">
              {recommendation.reason}
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
          <button
            onClick={() => onStartLesson?.(recommendation.lesson_id)}
            className="flex items-center justify-center gap-2 px-5 py-3 rounded-xs bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-mono font-bold text-xs uppercase tracking-wider transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)] cursor-pointer"
          >
            <span>START LESSON</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
