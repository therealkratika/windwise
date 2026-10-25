function formatDate(value) {
  return new Date(value).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function PeriodTable({ records }) {
  return (
    <div className="overflow-x-auto">
      <table className="mt-5 w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className="border-b border-slate-200 px-3 py-2.5 text-left text-[10px] uppercase tracking-[.04em] text-slate-400">Delivery period</th>
            <th className="border-b border-slate-200 px-3 py-2.5 text-left text-[10px] uppercase tracking-[.04em] text-slate-400">Forecast</th>
            <th className="border-b border-slate-200 px-3 py-2.5 text-left text-[10px] uppercase tracking-[.04em] text-slate-400">Actual</th>
            <th className="border-b border-slate-200 px-3 py-2.5 text-left text-[10px] uppercase tracking-[.04em] text-slate-400">Variance</th>
            <th className="border-b border-slate-200 px-3 py-2.5 text-left text-[10px] uppercase tracking-[.04em] text-slate-400">Shortfall</th>
          </tr>
        </thead>
        <tbody>
          {records.slice(0, 12).map((record) => (
            <tr key={record.startTime}>
              <td className="border-b border-slate-100 px-3 py-[13px] text-slate-600">{formatDate(record.startTime)}</td>
              <td className="border-b border-slate-100 px-3 py-[13px] text-slate-600">{record.forecast_mw.toFixed(1)} MW</td>
              <td className="border-b border-slate-100 px-3 py-[13px] text-slate-600">{record.actual_mw.toFixed(1)} MW</td>
              <td className={`border-b border-slate-100 px-3 py-[13px] ${record.error_mw > 0 ? 'text-amber-600' : 'text-[#2e9cac]'}`}>
                {record.error_mw > 0 ? '+' : ''}
                {record.error_mw.toFixed(1)} MW
              </td>
              <td className="border-b border-slate-100 px-3 py-[13px] text-slate-600">{record.wind_shortfall_mw.toFixed(1)} MW</td>
            </tr>
          ))}
        </tbody>
      </table>
      {records.length > 12 && <p className="mt-3.5 text-[11px] text-slate-400">Showing the first 12 matched periods.</p>}
    </div>
  )
}

export default PeriodTable
