import React, { useEffect } from 'react';
import { AlertTriangle, ArrowRight, X } from 'lucide-react';
import { useRealtime } from '../context/RealtimeContext';

/**
 * IncidentNotificationToast
 * Subtle in-cab banner notifying operator when a new incident is recorded by
 * the Edge Safety Engine. Clicking directly opens incident details.
 */
export default function IncidentNotificationToast({ onOpenIncident }) {
  const { newIncidentToast, dismissIncidentToast } = useRealtime();

  useEffect(() => {
    if (!newIncidentToast) return;
    const timer = setTimeout(() => {
      dismissIncidentToast();
    }, 15000);
    return () => clearTimeout(timer);
  }, [newIncidentToast, dismissIncidentToast]);

  if (!newIncidentToast) return null;

  const type = newIncidentToast.incident_type || 'HAZARD';
  const severity = newIncidentToast.severity || 'CRITICAL';
  const dist = newIncidentToast.proximity_distance_m !== undefined
    ? Number(newIncidentToast.proximity_distance_m).toFixed(1) + 'm'
    : null;

  const handleClick = () => {
    if (onOpenIncident && newIncidentToast.id) {
      onOpenIncident(newIncidentToast.id);
    }
    dismissIncidentToast();
  };

  return (
    <div className="fixed top-20 right-4 sm:right-6 z-40 max-w-md w-full animate-slide-in">
      <div className="bg-[#10131b] border-2 border-rose-500/80 rounded-sm shadow-[0_10px_30px_rgba(0,0,0,0.8),0_0_20px_rgba(244,63,94,0.3)] p-3.5 text-zinc-100 flex items-center justify-between gap-3">
        <div
          onClick={handleClick}
          className="flex items-center gap-3 cursor-pointer min-w-0 flex-1 hover:opacity-90 transition-opacity"
        >
          <div className="w-8 h-8 rounded-xs bg-rose-500/20 border border-rose-500/50 flex items-center justify-center text-rose-400 shrink-0">
            <AlertTriangle className="w-4 h-4 animate-pulse" />
          </div>

          <div className="min-w-0 space-y-0.5 font-mono">
            <div className="flex items-center gap-2 text-xs">
              <span className="font-bold text-white tracking-wider">NEW INCIDENT</span>
              <span className="text-zinc-500">•</span>
              <span className="text-zinc-300 font-semibold">{type}</span>
              <span className="px-1.5 py-0.2 rounded-xs bg-rose-600 text-white font-bold text-[10px]">
                {severity}
              </span>
              {dist && <span className="text-rose-400 font-bold text-xs">{dist}</span>}
            </div>
            <p className="text-[11px] text-zinc-400 truncate">
              {newIncidentToast.summary || 'Click to view physical telemetry context'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0 font-mono">
          <button
            onClick={handleClick}
            className="p-1.5 rounded-xs bg-white/[0.05] hover:bg-rose-500/20 text-zinc-300 hover:text-rose-300 border border-white/[0.08] transition-colors cursor-pointer"
            title="Inspect incident details"
          >
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={dismissIncidentToast}
            className="p-1.5 rounded-xs hover:bg-white/[0.08] text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer"
            title="Dismiss notification"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
