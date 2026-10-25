
import { useCallback, useEffect, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Database,
  RefreshCw,
} from 'lucide-react'

import { fetchAnalysis } from '../api'
import ForecastChart from '../components/ForecastChart'
import MetricCard from '../components/MetricCard'
import PeriodTable from '../components/PeriodTable'

const initialFilters = {
  start: '2026-01-01',
  end: '2026-02-01',
  cutoffHour: 10,
}

function formatNumber(value) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return '—'
  }

  return value.toLocaleString('en-GB', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
}

function Dashboard() {
  const [filters, setFilters] = useState(initialFilters)
  const [appliedFilters, setAppliedFilters] = useState(initialFilters)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  const invalidDateRange =
    !filters.start ||
    !filters.end ||
    filters.start >= filters.end

  const loadAnalysis = useCallback(async (selectedFilters) => {
    setLoading(true)
    setError('')

    try {
      const result = await fetchAnalysis(selectedFilters)

      setAnalysis(result)
      setAppliedFilters({ ...selectedFilters })
      setLastUpdated(new Date())
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to retrieve forecast analysis.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const initialLoad = setTimeout(() => {
      loadAnalysis(initialFilters)
    }, 0)

    return () => clearTimeout(initialLoad)
  }, [loadAnalysis])

  function updateFilter(event) {
    const { name, value } = event.target

    setFilters((current) => ({
      ...current,
      [name]: name === 'cutoffHour' ? Number(value) : value,
    }))
  }

  function handleSubmit(event) {
    event.preventDefault()

    if (invalidDateRange || loading) return

    loadAnalysis(filters)
  }

  const metrics = analysis?.metrics
  const records = analysis?.records ?? []
  const coverage = analysis?.coverage

  const biasDetail =
    metrics?.bias_mw == null
      ? 'Unavailable without matched data'
      : metrics.bias_mw > 0
        ? 'Wind generation tends to be overforecast'
        : metrics.bias_mw < 0
          ? 'Wind generation tends to be underforecast'
          : 'No average signed forecast error'

  const periodLabel = analysis?.period
    ? `${analysis.period.start} — ${analysis.period.end}`
    : `${appliedFilters.start} — ${appliedFilters.end}`

  return (
    <div className="min-h-screen bg-[#f7f9fa]">
      <main className="mx-auto w-full max-w-[1500px] min-w-0 px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
        {/* Page header */}
        <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-[.1em] text-[#2e9cac]">
              UK WIND GENERATION
            </p>

            <h1 className="font-display text-[clamp(28px,4vw,38px)] font-semibold tracking-[-.04em] text-[#172b32]">
              Forecast performance
            </h1>

            <p className="mt-2 max-w-2xl text-[13px] leading-6 text-slate-500">
              Evaluate day-ahead wind forecasts against realized national
              generation to support more informed electricity procurement.
            </p>
          </div>

          <div className="flex w-fit items-center gap-2 rounded-full border border-[#d9e9e4] bg-[#f2fbf7] px-3 py-2 text-xs font-semibold text-[#25815e]">
            <Database size={15} />
            Historical Elexon data
          </div>
        </header>

        {/* Filters */}
        <form
          onSubmit={handleSubmit}
          className="my-6 flex flex-wrap items-end gap-3 rounded-[10px] border border-slate-200 bg-white p-4 sm:my-8 sm:p-[18px]"
          aria-label="Analysis filters"
        >
          <div className="flex min-w-[140px] flex-1 flex-col gap-1.5">
            <label
              className="text-[11px] font-bold uppercase tracking-wide text-slate-500"
              htmlFor="start"
            >
              From
            </label>

            <input
              className="min-h-[40px] w-full rounded-md border border-slate-300 bg-white px-2.5 text-sm text-slate-700 outline-none transition focus:border-[#2e9cac] focus:ring-2 focus:ring-[#2e9cac]/15"
              id="start"
              name="start"
              type="date"
              value={filters.start}
              onChange={updateFilter}
              required
            />
          </div>

          <div className="flex min-w-[140px] flex-1 flex-col gap-1.5">
            <label
              className="text-[11px] font-bold uppercase tracking-wide text-slate-500"
              htmlFor="end"
            >
              To (exclusive)
            </label>

            <input
              className="min-h-[40px] w-full rounded-md border border-slate-300 bg-white px-2.5 text-sm text-slate-700 outline-none transition focus:border-[#2e9cac] focus:ring-2 focus:ring-[#2e9cac]/15"
              id="end"
              name="end"
              type="date"
              value={filters.end}
              onChange={updateFilter}
              required
            />
          </div>

          <div className="flex min-w-[155px] flex-1 flex-col gap-1.5">
            <label
              className="text-[11px] font-bold uppercase tracking-wide text-slate-500"
              htmlFor="cutoffHour"
            >
              Decision cutoff (UK)
            </label>

            <select
              className="min-h-[40px] w-full rounded-md border border-slate-300 bg-white px-2.5 text-sm text-slate-700 outline-none transition focus:border-[#2e9cac] focus:ring-2 focus:ring-[#2e9cac]/15"
              id="cutoffHour"
              name="cutoffHour"
              value={filters.cutoffHour}
              onChange={updateFilter}
            >
              <option value={8}>08:00</option>
              <option value={9}>09:00</option>
              <option value={10}>10:00</option>
              <option value={11}>11:00</option>
              <option value={12}>12:00</option>
            </select>
          </div>

          <button
            className="flex min-h-[40px] w-full items-center justify-center gap-2 rounded-md bg-[#1f7a8c] px-4 text-[13px] font-semibold text-white transition hover:bg-[#176371] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            type="submit"
            disabled={loading || invalidDateRange}
          >
            <RefreshCw
              size={15}
              className={loading ? 'animate-spin' : ''}
            />
            {loading ? 'Loading...' : 'Run analysis'}
          </button>
        </form>

        {invalidDateRange && (
          <div
            className="mb-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            role="alert"
          >
            <AlertCircle size={17} />
            Choose a valid start date earlier than the end date.
          </div>
        )}

        {/* Request error */}
        {error && (
          <div
            className="mb-5 flex items-start gap-3 rounded-lg border border-[#f2caca] bg-[#fff5f5] px-4 py-3 text-sm text-[#b73a3a]"
            role="alert"
          >
            <AlertCircle size={18} className="mt-0.5 shrink-0" />

            <div className="min-w-0 flex-1">
              <p className="font-semibold">Unable to refresh analysis</p>
              <p className="mt-1 break-words">{error}</p>
              {analysis && (
                <p className="mt-2 text-xs text-red-700">
                  Previously loaded results are still displayed for the last
                  successful filter selection.
                </p>
              )}
            </div>

            <button
              type="button"
              onClick={() => loadAnalysis(filters)}
              disabled={loading || invalidDateRange}
              className="shrink-0 rounded-md border border-red-200 px-3 py-1.5 text-xs font-semibold hover:bg-red-100 disabled:opacity-50"
            >
              Retry
            </button>
          </div>
        )}

        {/* Initial loading state */}
        {loading && !analysis && (
          <div
            className="grid min-h-[320px] place-items-center rounded-xl border border-slate-200 bg-white"
            role="status"
          >
            <div className="text-center">
              <RefreshCw
                size={25}
                className="mx-auto animate-spin text-[#2e9cac]"
              />
              <p className="mt-4 text-sm font-medium text-slate-600">
                Loading forecast performance...
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Retrieving Elexon generation records
              </p>
            </div>
          </div>
        )}

        {/* Analysis results */}
        {analysis && (
          <div className={loading ? 'opacity-60' : ''}>
            {/* Analysis summary */}
            <section
              className="mb-[18px] flex flex-wrap items-center gap-3 rounded-lg border border-[#d9e9e4] bg-[#f2fbf7] px-4 py-3"
              aria-label="Analysis status"
            >
              <CheckCircle2
                size={18}
                className="shrink-0 text-[#25815e]"
              />

              <div className="min-w-0 flex-1">
                <p className="text-[13px] font-semibold text-[#28765b]">
                  {metrics
                    ? `${metrics.matched_periods.toLocaleString()} matched half-hour periods`
                    : 'No matched periods found'}
                </p>

                <p className="mt-1 text-xs text-[#77968e]">
                  {periodLabel} · Decision cutoff{' '}
                  {String(appliedFilters.cutoffHour).padStart(2, '0')}:00 UK
                  time
                </p>
              </div>

              {lastUpdated && (
                <div className="flex items-center gap-1.5 text-[11px] text-[#77968e]">
                  <Clock3 size={13} />
                  <span>
                    Retrieved{' '}
                    {lastUpdated.toLocaleTimeString('en-GB', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              )}
            </section>

            {/* Coverage and data-quality context */}
            {coverage && (
              <section className="mb-[18px] grid grid-cols-2 gap-3 lg:grid-cols-3">
                <div className="rounded-lg border border-slate-200 bg-white p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Actual records
                  </p>
                  <p className="mt-2 text-xl font-semibold text-[#172b32]">
                    {coverage.actual_rows?.toLocaleString() ?? '—'}
                  </p>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Forecast records
                  </p>
                  <p className="mt-2 text-xl font-semibold text-[#172b32]">
                    {coverage.forecast_rows?.toLocaleString() ?? '—'}
                  </p>
                </div>

                <div className="col-span-2 rounded-lg border border-slate-200 bg-white p-4 lg:col-span-1">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Eligible forecasts
                  </p>
                  <p className="mt-2 text-xl font-semibold text-[#172b32]">
                    {coverage.eligible_forecasts?.toLocaleString() ?? '—'}
                  </p>
                </div>
              </section>
            )}

            {/* Key metrics */}
            <section
              className="mb-[18px] grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 lg:gap-[14px]"
              aria-label="Key metrics"
            >
              <MetricCard
                label="Mean absolute error"
                value={formatNumber(metrics?.mae_mw)}
                detail="Average absolute forecast error"
              />

              <MetricCard
                label="Root mean square error"
                value={formatNumber(metrics?.rmse_mw)}
                detail="Penalises larger forecast errors"
              />

              <MetricCard
                label="Forecast bias"
                value={formatNumber(metrics?.bias_mw)}
                detail={biasDetail}
              />

              <MetricCard
                label="Mean wind shortfall"
                value={formatNumber(metrics?.mean_wind_shortfall_mw)}
                detail="Average positive forecast-minus-actual difference"
              />
            </section>

            {/* Forecast chart */}
            <section className="mb-[18px] rounded-[10px] border border-slate-200 bg-white p-4 sm:p-[22px]">
              <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-display text-[17px] font-semibold tracking-[-.02em] text-[#172b32]">
                    Forecast vs actual generation
                  </h2>

                  <p className="mt-[7px] text-[13px] text-slate-500">
                    Half-hourly UK wind generation in megawatts
                  </p>
                </div>

                <span className="rounded-md bg-slate-50 px-2.5 py-1.5 text-[11px] text-slate-500">
                  {analysis.timezone || 'Europe/London'}
                </span>
              </div>

              {records.length > 0 ? (
                <ForecastChart records={records} />
              ) : (
                <div className="grid min-h-[220px] place-items-center text-center text-[13px] text-slate-500">
                  No matched chart data for this selection.
                </div>
              )}
            </section>

            {/* Delivery-period table */}
            <section className="mb-[18px] rounded-[10px] border border-slate-200 bg-white p-4 sm:p-[22px]">
              <div className="mb-5">
                <h2 className="font-display text-[17px] font-semibold tracking-[-.02em] text-[#172b32]">
                  Delivery-period breakdown
                </h2>

                <p className="mt-[7px] text-[13px] text-slate-500">
                  Forecast publication timestamps and realized generation
                </p>
              </div>

              {records.length > 0 ? (
                <PeriodTable records={records} />
              ) : (
                <div className="grid min-h-[180px] place-items-center text-center text-[13px] text-slate-500">
                  No matched periods to display.
                </div>
              )}
            </section>

            {/* Methodology */}
            <section className="rounded-lg border border-slate-200 bg-white p-4 sm:p-5">
              <h2 className="text-sm font-semibold text-[#172b32]">
                Methodology and interpretation
              </h2>

              <ul className="mt-3 space-y-2 text-xs leading-5 text-slate-500">
                <li>
                  <strong className="text-slate-700">Forecast error:</strong>{' '}
                  forecast generation minus actual generation. Positive bias
                  indicates overforecasting.
                </li>

                <li>
                  <strong className="text-slate-700">MAE:</strong>{' '}
                  average absolute error across matched delivery periods.
                </li>

                <li>
                  <strong className="text-slate-700">RMSE:</strong>{' '}
                  square root of mean squared error, giving larger errors
                  greater influence.
                </li>

                <li>
                  <strong className="text-slate-700">Wind shortfall:</strong>{' '}
                  positive forecast-minus-actual difference. It is not the
                  utility's total procurement requirement.
                </li>

                <li>
                  <strong className="text-slate-700">Decision cutoff:</strong>{' '}
                  the configured previous-day UK local time. Validate the
                  actual trading deadline before using these results for
                  operational decisions.
                </li>
              </ul>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default Dashboard
