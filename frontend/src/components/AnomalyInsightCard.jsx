import React from 'react';
import { BrainCircuit, Activity, ArrowRight } from 'lucide-react';

export default function AnomalyInsightCard({ insight, modelHealth, onOpenInsights }) {
  const ready = Boolean(modelHealth?.model_loaded);
  if (!ready) {
    return (
      <div className="glass-panel hud-corner p-4 rounded-sm border border-white/[0.07]">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <BrainCircuit className="w-5 h-5 text-zinc-500" />
            <div>
              <div className="text-[10px] font-mono tracking-wider text-zinc-400">ANOMALY ANALYTICS</div>
              <div className="text-sm font-semibold text-zinc-300">ANALYTICS UNAVAILABLE</div>
            </div>
          </div>
          <span className="text-[10px] font-mono text-zinc-500">SAFETY UNAFFECTED</span>
        </div>
      </div>
    );
  }

  if (!insight) return null;
  const unusual = insight.is_anomaly;
  const primary = insight.evidence?.[0];

  return (
    <div className={`glass-panel hud-corner p-4 rounded-sm border ${
      unusual ? 'border-amber-500/35' : 'border-emerald-500/25'
    }`}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className={`w-9 h-9 rounded-xs border flex items-center justify-center ${
            unusual ? 'bg-amber-500/10 border-amber-500/35' : 'bg-emerald-500/10 border-emerald-500/30'
          }`}>
            <Activity className={`w-4 h-4 ${unusual ? 'text-amber-400' : 'text-emerald-400'}`} />
          </div>
          <div className="min-w-0">
            <div className="text-[10px] font-mono tracking-wider text-zinc-400">ADVISORY ANALYTICS · MODEL {insight.model_version}</div>
            <div className={`text-sm font-semibold tracking-wide ${unusual ? 'text-amber-300' : 'text-emerald-300'}`}>
              {unusual ? 'UNUSUAL OPERATING PATTERN' : 'OPERATING PATTERN NOMINAL'}
            </div>
            <div className="text-xs font-mono text-zinc-400 truncate">
              {unusual ? insight.anomaly_type.replaceAll('_', ' ') : 'No unusual pattern detected in latest window'}
              {primary ? ` · ${primary.message}` : ''}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[9px] font-mono text-zinc-500">MODEL SCORE</div>
            <div className="mono-value text-lg text-zinc-200">{Math.round(insight.anomaly_score * 100)}%</div>
          </div>
          <button
            onClick={onOpenInsights}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xs border border-white/[0.1] bg-white/[0.03] hover:bg-white/[0.06] text-xs font-mono text-zinc-300 cursor-pointer"
          >
            DETAILS <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
