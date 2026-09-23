import React from 'react';
import { History, CheckCircle2, XCircle, Award } from 'lucide-react';

/**
 * TrainingHistory
 * Displays record of completed coaching modules, dates, and scores.
 */
export default function TrainingHistory({ history = [] }) {
  if (!history || history.length === 0) {
    return (
      <div className="glass-panel p-5 rounded-xs border border-white/[0.08] text-center space-y-2">
        <History className="w-6 h-6 text-zinc-500 mx-auto" />
        <h4 className="text-xs font-mono font-semibold text-zinc-300 uppercase">
          NO TRAINING RECORDS FOUND
        </h4>
        <p className="text-[11px] font-mono text-zinc-400">
          Completed coaching modules will appear here with verification scores.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-emerald-400" />
          <h2 className="text-xs font-mono font-bold tracking-wider text-zinc-200 uppercase">
            CERTIFICATION & COMPLETION HISTORY
          </h2>
        </div>
        <span className="text-[10px] font-mono text-zinc-400">
          {history.length} COMPLETED SESSIONS
        </span>
      </div>

      <div className="glass-panel rounded-xs border border-white/[0.08] overflow-hidden">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] bg-[#12151d] text-[10px] uppercase text-zinc-400">
              <th className="py-2.5 px-4">Lesson</th>
              <th className="py-2.5 px-4">Operator</th>
              <th className="py-2.5 px-4">Completed Date</th>
              <th className="py-2.5 px-4 text-right">Score</th>
              <th className="py-2.5 px-4 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.05]">
            {history.map((item) => (
              <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-4 font-semibold text-white">
                  <div className="flex flex-col">
                    <span>{item.lesson_title}</span>
                    <span className="text-[10px] text-zinc-400">{item.lesson_id}</span>
                  </div>
                </td>
                <td className="py-3 px-4 text-zinc-300">
                  {item.operator_id}
                </td>
                <td className="py-3 px-4 text-zinc-400 text-[11px]">
                  {item.completed_at ? item.completed_at.slice(0, 16).replace('T', ' ') + ' UTC' : '—'}
                </td>
                <td className="py-3 px-4 text-right font-bold text-white">
                  {item.score_pct}%
                </td>
                <td className="py-3 px-4 text-center">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-xs text-[10px] font-bold uppercase ${
                    item.passed
                      ? 'bg-emerald-950/60 border border-emerald-500/40 text-emerald-300'
                      : 'bg-red-950/60 border border-red-500/40 text-red-300'
                  }`}>
                    {item.passed ? (
                      <>
                        <CheckCircle2 className="w-3 h-3" />
                        PASSED
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3 h-3" />
                        FAILED
                      </>
                    )}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
