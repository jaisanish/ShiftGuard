import React from 'react';

/**
 * Sparkline
 * Compact rolling SVG sparkline for high-frequency telemetry trends.
 * Supports dynamic min/max scaling or fixed range bounds, with optional gradient fill.
 */
export default function Sparkline({
  data = [],
  color = '#10b981',
  height = 24,
  minBound = null,
  maxBound = null,
  showGradient = true,
  id = 'spark',
}) {
  if (!data || data.length < 2) {
    return (
      <div
        className="w-full rounded-xs bg-white/[0.02] border border-white/[0.04] flex items-center justify-center"
        style={{ height: `${height}px` }}
      >
        <span className="text-[9px] font-mono text-zinc-600">AWAITING SAMPLES</span>
      </div>
    );
  }

  const values = data.map((v) => (typeof v === 'number' && !isNaN(v) ? v : 0));
  const dataMin = minBound !== null ? minBound : Math.min(...values);
  const dataMax = maxBound !== null ? maxBound : Math.max(...values);
  const range = dataMax - dataMin === 0 ? 1 : dataMax - dataMin;

  const width = 100;
  const paddingY = 2;
  const usableHeight = height - paddingY * 2;

  // Generate points for SVG path
  const points = values.map((val, idx) => {
    const x = (idx / (values.length - 1)) * width;
    const clampedVal = Math.max(dataMin, Math.min(dataMax, val));
    const normalizedY = (clampedVal - dataMin) / range;
    const y = height - paddingY - normalizedY * usableHeight;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const pathD = `M ${points.join(' L ')}`;
  const areaD = `${pathD} L ${width},${height} L 0,${height} Z`;
  const gradId = `spark-grad-${id}`;

  return (
    <div className="w-full relative overflow-hidden" style={{ height: `${height}px` }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full overflow-visible"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0.28" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {showGradient && (
          <path d={areaD} fill={`url(#${gradId})`} />
        )}

        <path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Current latest point dot */}
        {points.length > 0 && (
          <circle
            cx={points[points.length - 1].split(',')[0]}
            cy={points[points.length - 1].split(',')[1]}
            r="2"
            fill={color}
          />
        )}
      </svg>
    </div>
  );
}
