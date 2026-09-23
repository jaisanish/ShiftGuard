import React, { useEffect, useState } from 'react';
import { BrainCircuit, Database, Gauge, ShieldCheck } from 'lucide-react';
import { useRealtime } from '../context/RealtimeContext';
import { fetchAnomalies, fetchOperatorBaseline } from '../services/api';

const LABELS = {
  idle_ratio: 'Idle ratio',
  fuel_per_load_cycle: 'Fuel / cycle',
  load_cycles_per_hour: 'Cycles / hour',
  fuel_per_active_hour: 'Fuel / active hour',
  safety_alert_rate: 'Safety-event rate',
  seatbelt_violation_rate: 'Seatbelt-violation rate',
};

export default function AnalyticsPage() {
  const { anomalyInsight, anomalyModelHealth, telemetry, selectedMachineId } = useRealtime();
  const operatorId = telemetry?.operator_id || 'OP-101';
  const [baseline, setBaseline] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    Promise.all([
      fetchOperatorBaseline(operatorId),
      fetchAnomalies({ machine_id: selectedMachineId, operator_id: operatorId, limit: 20 }),
    ]).then(([profile, records]) => {
      setBaseline(profile);
      setHistory(records);
    });
  }, [operatorId, selectedMachineId]);

  if (!anomalyModelHealth?.model_loaded) {
    return (
      <div className="glass-panel p-8 rounded-sm text-center space-y-3">
        <BrainCircuit className="w-8 h-8 text-zinc-500 mx-auto" />
        <h1 className="display-heading text-xl text-zinc-200">ANALYTICS UNAVAILABLE</h1>
        <p className="text-xs font-mono text-zinc-400">The versioned anomaly model could not be loaded. Edge safety remains fully operational.</p>
      </div>
    );
  }

  return (
    <section className="space-y-5">
      <div className="glass-panel hud-corner p-5 rounded-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-emerald-400">
            <BrainCircuit className="w-5 h-5" />
            <h1 className="display-heading text-xl font-semibold text-zinc-100">OPERATING INSIGHTS</h1>
          </div>
          <p className="text-xs font-mono text-zinc-400 mt-1">Advisory Isolation Forest analytics · never used for immediate safety decisions</p>
        </div>
        <div className="flex gap-3 text-[10px] font-mono">
          <span className="px-2 py-1 border border-emerald-500/30 bg-emerald-500/10 text-emerald-300">MODEL {anomalyModelHealth.model_version}</span>
          <span className="px-2 py-1 border border-white/[0.08] bg-white/[0.03] text-zinc-300">15 MIN WINDOWS</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="glass-panel p-5 rounded-sm lg:col-span-2">
          <div className="text-[10px] font-mono tracking-wider text-zinc-400 mb-3">LATEST ACTUAL MODEL INFERENCE</div>
          {anomalyInsight ? (
            <div className="space-y-4">
              <div className="flex items-end justify-between gap-3">
                <div>
                  <div className={`text-lg font-semibold ${anomalyInsight.is_anomaly ? 'text-amber-300' : 'text-emerald-300'}`}>
                    {anomalyInsight.anomaly_type.replaceAll('_', ' ')}
                  </div>
                  <div className="text-[11px] font-mono text-zinc-500">{anomalyInsight.window_start} → {anomalyInsight.window_end}</div>
                </div>
                <div className="text-right">
                  <div className="text-[9px] font-mono text-zinc-500">ANOMALY SCORE</div>
                  <div className="mono-value text-3xl text-zinc-100">{Math.round(anomalyInsight.anomaly_score * 100)}%</div>
                </div>
              </div>
              <div className="space-y-2">
                {(anomalyInsight.evidence || []).map((item) => (
                  <div key={item.feature} className="p-3 bg-[#11141c]/70 border border-white/[0.06] rounded-xs">
                    <div className="flex justify-between gap-4 text-xs font-mono">
                      <span className="text-zinc-200">{LABELS[item.feature] || item.feature}</span>
                      <span className="text-zinc-400">CURRENT {item.current_value.toFixed(2)} · BASELINE {item.baseline_value.toFixed(2)}</span>
                    </div>
                    <p className="text-[10px] text-zinc-500 mt-1">{item.message}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : <p className="text-xs font-mono text-zinc-500">No complete feature window is available.</p>}
        </div>

        <div className="glass-panel p-5 rounded-sm space-y-4">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-300"><Database className="w-4 h-4 text-emerald-400" /> BASELINE PROFILE</div>
          <div>
            <div className="text-sm font-semibold text-zinc-200">{baseline?.source?.replaceAll('_', ' ') || 'LOADING'}</div>
            <div className="text-[10px] font-mono text-zinc-500">{baseline?.window_count || 0} historical windows</div>
          </div>
          <div className="border-t border-white/[0.06] pt-3 flex items-center gap-2 text-[10px] font-mono text-zinc-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> SAFETY AUTHORITY: LOCAL EDGE ONLY
          </div>
        </div>
      </div>

      <div className="glass-panel p-5 rounded-sm">
        <div className="flex items-center gap-2 text-xs font-mono text-zinc-300 mb-3"><Gauge className="w-4 h-4 text-emerald-400" /> PERSISTED UNUSUAL PATTERNS</div>
        {history.length === 0 ? (
          <p className="text-xs font-mono text-zinc-500">NO UNUSUAL PATTERNS PERSISTED</p>
        ) : (
          <div className="space-y-2">
            {history.map((item) => (
              <div key={item.id} className="grid grid-cols-2 md:grid-cols-4 gap-2 p-3 bg-[#11141c]/60 border border-white/[0.05] text-xs font-mono">
                <span className="text-amber-300">{item.anomaly_type.replaceAll('_', ' ')}</span>
                <span className="text-zinc-300">Score {Math.round(item.anomaly_score * 100)}%</span>
                <span className="text-zinc-400">{item.machine_id}</span>
                <span className="text-zinc-500">{item.window_end}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
