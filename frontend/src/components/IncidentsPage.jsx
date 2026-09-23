import React, { useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Compass,
  FileText,
  Mountain,
  X,
  Activity,
  Radar,
} from 'lucide-react';
import { useRealtime } from '../context/RealtimeContext';

/**
 * IncidentsPage
 * Comprehensive log of safety incidents recorded by the Edge Safety Engine.
 * Supports clicking an incident to inspect real Pre-Event, Trigger, and Post-Event
 * physical telemetry context buffers stored in edge SQLite.
 */
export default function IncidentsPage() {
  const {
    incidents,
    selectedIncident,
    loadingIncidentDetail,
    openIncidentDetail,
    closeIncidentDetail,
    acknowledgeIncident,
  } = useRealtime();

  const [activeContextTab, setActiveContextTab] = useState('trigger'); // 'pre' | 'trigger' | 'post'

  const handleAcknowledge = async (id) => {
    await acknowledgeIncident(id);
  };

  return (
    <div className="space-y-5 animate-fade-in font-mono">
      {/* 1. Incidents Header */}
      <div className="glass-panel p-4 sm:p-5 rounded-sm border border-white/[0.08] flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-400">
              SAFETY INCIDENTS LOG
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-xs bg-rose-950/60 border border-rose-500/40 text-rose-300 font-semibold">
              CRITICAL AUDIT TRAIL
            </span>
          </div>
          <p className="text-xs text-zinc-300 mt-0.5">
            Full physical telemetry context buffers captured at the moment of rule violations.
          </p>
        </div>

        <div className="text-xs text-zinc-400">
          TOTAL RECORDED: <strong className="text-white">{incidents.length}</strong>
        </div>
      </div>

      {/* 2. Incidents List Table */}
      <div className="glass-panel p-5 rounded-sm space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 text-xs">
          <div className="flex items-center gap-2 font-semibold uppercase text-zinc-200">
            <FileText className="w-4 h-4 text-emerald-400" />
            <span>INCIDENT REGISTRY</span>
          </div>
          <span className="text-[10px] text-zinc-400">
            CLICK ROW TO INSPECT CONTEXT BUFFER
          </span>
        </div>

        {incidents.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <CheckCircle2 className="w-10 h-10 text-emerald-400/80 mx-auto" />
            <div className="text-base font-bold text-zinc-200 tracking-wider">
              NO INCIDENTS RECORDED
            </div>
            <p className="text-xs text-zinc-400 max-w-md mx-auto">
              The Edge Safety Engine has not recorded any critical safety incidents during this shift.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/[0.08] text-zinc-400 text-[11px]">
                  <th className="pb-2.5">TIME (UTC)</th>
                  <th className="pb-2.5">TYPE</th>
                  <th className="pb-2.5">SEVERITY</th>
                  <th className="pb-2.5">MACHINE</th>
                  <th className="pb-2.5">TASK</th>
                  <th className="pb-2.5">SUMMARY</th>
                  <th className="pb-2.5">STATUS</th>
                  <th className="pb-2.5 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {incidents.map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => openIncidentDetail(inc.id)}
                    className="hover:bg-white/[0.03] transition-colors cursor-pointer group"
                  >
                    <td className="py-3 text-zinc-300">
                      {inc.triggered_at ? inc.triggered_at.slice(11, 19) : inc.timestamp?.slice(11, 19) || '—'}
                    </td>
                    <td className="py-3 font-bold text-white group-hover:text-emerald-300 transition-colors">
                      {inc.incident_type}
                    </td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-0.5 rounded-xs text-[10px] font-bold ${
                          inc.severity === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        }`}
                      >
                        {inc.severity}
                      </span>
                    </td>
                    <td className="py-3 text-zinc-300 font-semibold">{inc.machine_id}</td>
                    <td className="py-3 text-zinc-400">{inc.task_id || 'UNKNOWN'}</td>
                    <td className="py-3 text-zinc-300 max-w-xs truncate">{inc.summary}</td>
                    <td className="py-3">
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded-xs ${
                          inc.status === 'RESOLVED'
                            ? 'bg-zinc-800 text-zinc-300 border border-zinc-700'
                            : inc.status === 'ACKNOWLEDGED'
                            ? 'bg-blue-950/60 text-blue-300 border border-blue-500/40'
                            : 'bg-rose-950/60 text-rose-300 border border-rose-500/40 animate-pulse'
                        }`}
                      >
                        {inc.status}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openIncidentDetail(inc.id);
                        }}
                        className="px-2.5 py-1 rounded-xs bg-white/[0.05] hover:bg-emerald-500/20 text-zinc-300 hover:text-emerald-300 border border-white/[0.08] transition-colors cursor-pointer text-[11px]"
                      >
                        INSPECT
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 3. Incident Context Detail Modal / Drawer */}
      {selectedIncident && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
        >
          <div className="relative w-full max-w-4xl max-h-[90vh] bg-[#0d1017] border border-white/[0.12] rounded-sm shadow-2xl flex flex-col overflow-hidden text-zinc-100">
            {/* Modal Header */}
            <div className="p-4 sm:p-5 border-b border-white/[0.08] flex items-center justify-between gap-4 bg-[#121620]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xs bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
                  <AlertOctagon className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-bold text-white uppercase tracking-wider">
                      INCIDENT CONTEXT AUDIT
                    </span>
                    <span className="px-1.5 py-0.2 rounded-xs bg-rose-600 text-white font-bold text-[10px]">
                      {selectedIncident.severity}
                    </span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-xs ${
                      selectedIncident.status === 'RESOLVED'
                        ? 'bg-zinc-800 text-zinc-300'
                        : selectedIncident.status === 'ACKNOWLEDGED'
                        ? 'bg-blue-900/60 text-blue-300'
                        : 'bg-rose-950/60 text-rose-300'
                    }`}>
                      {selectedIncident.status}
                    </span>
                  </div>
                  <span className="text-[10px] text-zinc-400">ID: {selectedIncident.id}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {selectedIncident.status === 'OPEN' && (
                  <button
                    onClick={() => handleAcknowledge(selectedIncident.id)}
                    className="px-3 py-1.5 rounded-xs bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold uppercase transition-colors cursor-pointer"
                  >
                    ACKNOWLEDGE
                  </button>
                )}
                <button
                  onClick={closeIncidentDetail}
                  className="p-1.5 rounded-xs hover:bg-white/[0.08] text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body (Scrollable) */}
            <div className="p-4 sm:p-6 overflow-y-auto space-y-5 text-xs">
              {/* Primary Incident Parameters Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-[#141822] border border-white/[0.06] p-3 rounded-xs">
                  <span className="text-[10px] text-zinc-400 uppercase block">INCIDENT TYPE</span>
                  <strong className="text-white text-sm">{selectedIncident.incident_type}</strong>
                </div>

                <div className="bg-[#141822] border border-white/[0.06] p-3 rounded-xs">
                  <span className="text-[10px] text-zinc-400 uppercase block">TIMESTAMP (UTC)</span>
                  <strong className="text-white text-sm">
                    {selectedIncident.triggered_at ? selectedIncident.triggered_at.slice(11, 19) + ' UTC' : '—'}
                  </strong>
                </div>

                <div className="bg-[#141822] border border-white/[0.06] p-3 rounded-xs">
                  <span className="text-[10px] text-zinc-400 uppercase block">MACHINE</span>
                  <strong className="text-emerald-400 text-sm">{selectedIncident.machine_id}</strong>
                </div>

                <div className="bg-[#141822] border border-white/[0.06] p-3 rounded-xs">
                  <span className="text-[10px] text-zinc-400 uppercase block">OPERATOR</span>
                  <strong className="text-white text-sm">OPERATOR 1</strong>
                </div>

                <div className="bg-[#141822] border border-white/[0.06] p-3 rounded-xs">
                  <span className="text-[10px] text-zinc-400 uppercase block">TASK ID</span>
                  <strong className="text-white text-sm">{selectedIncident.task_id || 'UNKNOWN'}</strong>
                </div>

                <div className="bg-[#141822] border border-white/[0.06] p-3 rounded-xs">
                  <span className="text-[10px] text-zinc-400 uppercase block">ZONE</span>
                  <strong className="text-white text-sm">{selectedIncident.gps_zone || 'UNKNOWN'}</strong>
                </div>

                <div className="bg-[#141822] border border-white/[0.06] p-3 rounded-xs">
                  <span className="text-[10px] text-zinc-400 uppercase block">DISTANCE AT TRIGGER</span>
                  <strong className="text-rose-400 text-sm">
                    {selectedIncident.context_buffer?.trigger_event?.proximity_distance_m !== undefined
                      ? `${selectedIncident.context_buffer.trigger_event.proximity_distance_m.toFixed(1)} m`
                      : 'N/A'}
                  </strong>
                </div>

                <div className="bg-[#141822] border border-white/[0.06] p-3 rounded-xs">
                  <span className="text-[10px] text-zinc-400 uppercase block">OPERATING STATE</span>
                  <strong className="text-white text-sm uppercase">
                    {selectedIncident.context_buffer?.trigger_event?.operating_state || 'UNKNOWN'}
                  </strong>
                </div>
              </div>

              {/* Incident Summary */}
              <div className="bg-rose-950/20 border border-rose-500/30 p-3.5 rounded-xs">
                <span className="text-[10px] text-rose-300 font-bold uppercase tracking-wider block mb-1">
                  RULE VIOLATION SUMMARY
                </span>
                <p className="text-rose-100">{selectedIncident.summary}</p>
              </div>

              {/* Context Buffer Visualization Tabs */}
              <div className="space-y-3">
                <div className="flex items-center gap-1 border-b border-white/[0.08] pb-1">
                  <button
                    onClick={() => setActiveContextTab('pre')}
                    className={`px-3 py-1.5 rounded-xs font-semibold text-xs tracking-wider cursor-pointer ${
                      activeContextTab === 'pre'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    PRE-EVENT ({selectedIncident.context_buffer?.pre_event?.length || 0} FRAMES)
                  </button>

                  <button
                    onClick={() => setActiveContextTab('trigger')}
                    className={`px-3 py-1.5 rounded-xs font-semibold text-xs tracking-wider cursor-pointer ${
                      activeContextTab === 'trigger'
                        ? 'bg-rose-600/30 text-rose-300 border border-rose-500/50'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    TRIGGER EVENT
                  </button>

                  <button
                    onClick={() => setActiveContextTab('post')}
                    className={`px-3 py-1.5 rounded-xs font-semibold text-xs tracking-wider cursor-pointer ${
                      activeContextTab === 'post'
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    POST-EVENT ({selectedIncident.context_buffer?.post_event?.length || 0} FRAMES)
                  </button>
                </div>

                {/* Tab: Trigger Event */}
                {activeContextTab === 'trigger' && (
                  <div className="p-4 rounded-xs bg-[#10141e] border-2 border-rose-500/50 space-y-3">
                    <div className="flex items-center justify-between text-xs text-rose-400 font-bold">
                      <span>TRIGGER FRAME DETECTED BY EDGE ENGINE</span>
                      <span>{selectedIncident.context_buffer?.trigger_event?.timestamp || selectedIncident.triggered_at}</span>
                    </div>

                    {selectedIncident.context_buffer?.trigger_event ? (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-[11px]">
                        <div className="bg-black/40 p-2 rounded-xs">
                          <span className="text-zinc-400 block">Proximity Distance:</span>
                          <strong className="text-rose-400 text-sm">
                            {selectedIncident.context_buffer.trigger_event.proximity_distance_m !== undefined
                              ? `${selectedIncident.context_buffer.trigger_event.proximity_distance_m.toFixed(1)} m`
                              : '—'}
                          </strong>
                        </div>
                        <div className="bg-black/40 p-2 rounded-xs">
                          <span className="text-zinc-400 block">Ground Speed:</span>
                          <strong className="text-white text-sm">
                            {selectedIncident.context_buffer.trigger_event.machine_speed_kmh?.toFixed(1) || '0.0'} km/h
                          </strong>
                        </div>
                        <div className="bg-black/40 p-2 rounded-xs">
                          <span className="text-zinc-400 block">Engine RPM:</span>
                          <strong className="text-white text-sm">
                            {selectedIncident.context_buffer.trigger_event.engine_rpm?.toFixed(0) || '0'}
                          </strong>
                        </div>
                        <div className="bg-black/40 p-2 rounded-xs">
                          <span className="text-zinc-400 block">Seatbelt State:</span>
                          <strong className={selectedIncident.context_buffer.trigger_event.seatbelt_status === 'FASTENED' ? 'text-emerald-400 text-sm' : 'text-rose-400 text-sm'}>
                            {selectedIncident.context_buffer.trigger_event.seatbelt_status || 'FASTENED'}
                          </strong>
                        </div>
                      </div>
                    ) : (
                      <p className="text-zinc-400">Trigger frame evidence unavailable.</p>
                    )}
                  </div>
                )}

                {/* Tab: Pre-Event Frames */}
                {activeContextTab === 'pre' && (
                  <div className="space-y-2">
                    <span className="text-[11px] text-zinc-400">
                      Telemetry sliding buffer recorded up to 30 seconds prior to incident trigger:
                    </span>
                    {(!selectedIncident.context_buffer?.pre_event || selectedIncident.context_buffer.pre_event.length === 0) ? (
                      <p className="p-4 bg-[#141822] rounded-xs text-zinc-400 text-center">
                        No pre-event frames in sliding buffer (incident occurred at telemetry start).
                      </p>
                    ) : (
                      <div className="overflow-x-auto max-h-48 border border-white/[0.06] rounded-xs">
                        <table className="w-full text-left text-[11px]">
                          <thead className="bg-[#141822] text-zinc-400 sticky top-0">
                            <tr>
                              <th className="p-2">TIME</th>
                              <th className="p-2">SPEED</th>
                              <th className="p-2">RPM</th>
                              <th className="p-2">LOAD %</th>
                              <th className="p-2">PROXIMITY</th>
                              <th className="p-2">STATE</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/[0.04]">
                            {selectedIncident.context_buffer.pre_event.map((f, idx) => (
                              <tr key={idx} className="hover:bg-white/[0.02]">
                                <td className="p-2 text-zinc-300">{f.timestamp?.slice(11, 19)}</td>
                                <td className="p-2 text-white">{f.machine_speed_kmh?.toFixed(1)} km/h</td>
                                <td className="p-2 text-white">{f.engine_rpm?.toFixed(0)}</td>
                                <td className="p-2 text-white">{f.engine_load_pct?.toFixed(1)}%</td>
                                <td className="p-2 text-rose-300">{f.proximity_distance_m?.toFixed(1)} m</td>
                                <td className="p-2 text-zinc-400 uppercase">{f.operating_state}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab: Post-Event Frames */}
                {activeContextTab === 'post' && (
                  <div className="space-y-2">
                    <span className="text-[11px] text-zinc-400">
                      Telemetry frames accumulated after trigger until resolution:
                    </span>
                    {(!selectedIncident.context_buffer?.post_event || selectedIncident.context_buffer.post_event.length === 0) ? (
                      <p className="p-4 bg-[#141822] rounded-xs text-zinc-400 text-center">
                        Post-event recovery frames have not been recorded or incident is still actively unfolding.
                      </p>
                    ) : (
                      <div className="overflow-x-auto max-h-48 border border-white/[0.06] rounded-xs">
                        <table className="w-full text-left text-[11px]">
                          <thead className="bg-[#141822] text-zinc-400 sticky top-0">
                            <tr>
                              <th className="p-2">TIME</th>
                              <th className="p-2">SPEED</th>
                              <th className="p-2">RPM</th>
                              <th className="p-2">LOAD %</th>
                              <th className="p-2">PROXIMITY</th>
                              <th className="p-2">STATE</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/[0.04]">
                            {selectedIncident.context_buffer.post_event.map((f, idx) => (
                              <tr key={idx} className="hover:bg-white/[0.02]">
                                <td className="p-2 text-zinc-300">{f.timestamp?.slice(11, 19)}</td>
                                <td className="p-2 text-white">{f.machine_speed_kmh?.toFixed(1)} km/h</td>
                                <td className="p-2 text-white">{f.engine_rpm?.toFixed(0)}</td>
                                <td className="p-2 text-white">{f.engine_load_pct?.toFixed(1)}%</td>
                                <td className="p-2 text-rose-300">{f.proximity_distance_m?.toFixed(1)} m</td>
                                <td className="p-2 text-zinc-400 uppercase">{f.operating_state}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-white/[0.08] flex justify-end bg-[#121620]">
              <button
                onClick={closeIncidentDetail}
                className="px-4 py-2 rounded-xs bg-white/[0.08] hover:bg-white/[0.15] text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer"
              >
                CLOSE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
