
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'

function MetricCard({ label, value, unit = 'MW', detail, trend }) {
  const hasTrend = typeof trend === 'number'
  const isPositive = hasTrend && trend > 0
  const isNegative = hasTrend && trend < 0

  const trendColor = isPositive
    ? 'text-amber-600'
    : isNegative
      ? 'text-[#2e9cac]'
      : 'text-slate-500'

  const TrendIcon = isPositive
    ? ArrowUpRight
    : isNegative
      ? ArrowDownRight
      : Minus

  return (
    <article className="min-h-[142px] rounded-[10px] border border-slate-200 bg-white p-5">
      <p className="mb-[13px] text-xs font-semibold text-slate-500">
        {label}
      </p>

      <div className="flex items-baseline gap-[5px]">
        <strong className="font-display text-[28px] font-semibold text-[#172b32]">
          {value ?? '—'}
        </strong>

        {value != null && unit && (
          <span className="text-xs text-slate-400">{unit}</span>
        )}
      </div>

      {detail && (
        <p className="mt-[7px] text-[11px] text-slate-400">
          {detail}
        </p>
      )}

      {hasTrend && (
        <span
          className={`mt-[9px] flex items-center gap-[3px] text-[10px] font-semibold ${trendColor}`}
          aria-label={`${Math.abs(trend).toFixed(1)} percent ${
            isPositive ? 'increase' : isNegative ? 'decrease' : 'change of zero'
          } versus previous period`}
        >
          <TrendIcon size={15} aria-hidden="true" />
          {Math.abs(trend).toFixed(1)}% vs previous period
        </span>
      )}
    </article>
  )
}

export default MetricCard
