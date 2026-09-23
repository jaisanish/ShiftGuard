import React from 'react';

/**
 * TelemetryValue
 * Tactile industrial metric display with high readability, unit badges, and semantic color accents.
 */
export default function TelemetryValue({
  label,
  value,
  unit,
  status = 'normal', // 'normal' | 'safe' | 'warning' | 'critical' | 'inactive'
  subtext,
  icon: Icon,
  size = 'md', // 'sm' | 'md' | 'lg'
}) {
  const statusStyles = {
    normal: {
      border: 'border-white/[0.08]',
      text: 'text-zinc-100',
      badge: 'text-zinc-400 bg-zinc-800/60',
      glow: '',
    },
    safe: {
      border: 'border-emerald-500/30',
      text: 'text-emerald-400',
      badge: 'text-emerald-300 bg-emerald-950/60 border border-emerald-500/20',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.1)]',
    },
    warning: {
      border: 'border-amber-500/40',
      text: 'text-amber-400',
      badge: 'text-amber-300 bg-amber-950/60 border border-amber-500/20',
      glow: 'shadow-[0_0_15px_rgba(245,158,11,0.15)]',
    },
    critical: {
      border: 'border-rose-500/50',
      text: 'text-rose-400',
      badge: 'text-rose-300 bg-rose-950/60 border border-rose-500/30',
      glow: 'shadow-[0_0_20px_rgba(239,68,68,0.2)]',
    },
    inactive: {
      border: 'border-white/[0.04]',
      text: 'text-zinc-500',
      badge: 'text-zinc-600 bg-zinc-900/60',
      glow: '',
    },
  };

  const currentStatus = statusStyles[status] || statusStyles.normal;

  return (
    <div
      className={`glass-panel hud-corner p-3.5 sm:p-4 rounded-sm flex flex-col justify-between relative overflow-hidden transition-all duration-200 ${currentStatus.border} ${currentStatus.glow}`}
    >
      {/* Top row: Label & Icon */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-semibold tracking-wider text-zinc-400 uppercase font-mono">
          {label}
        </span>
        {Icon && <Icon className="w-3.5 h-3.5 text-zinc-500 shrink-0" />}
      </div>

      {/* Main value display */}
      <div className="flex items-baseline gap-1.5 my-0.5">
        <span
          className={`mono-value font-bold tracking-tight ${
            size === 'lg'
              ? 'text-3xl sm:text-4xl'
              : size === 'sm'
              ? 'text-lg sm:text-xl'
              : 'text-2xl sm:text-3xl'
          } ${currentStatus.text}`}
        >
          {value !== undefined && value !== null ? value : '--'}
        </span>
        {unit && (
          <span className="text-xs font-mono text-zinc-400 font-medium tracking-tight">
            {unit}
          </span>
        )}
      </div>

      {/* Subtext or secondary indicator */}
      {subtext && (
        <div className="mt-1 text-[10px] font-mono text-zinc-400 tracking-wide flex items-center gap-1.5">
          {subtext}
        </div>
      )}
    </div>
  );
}
