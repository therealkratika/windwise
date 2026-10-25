import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function formatTime(value) {
  return new Date(value).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
  })
}

function ForecastChart({ records }) {
  const data = records.map((record) => ({
    ...record,
    date: formatTime(record.startTime),
    forecast: Number(record.forecast_mw.toFixed(1)),
    actual: Number(record.actual_mw.toFixed(1)),
  }))

  return (
    <div className="my-5 -mx-1 -mb-2">
      <ResponsiveContainer width="100%" height={310}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: -14, bottom: 4 }}>
          <CartesianGrid stroke="#e8edf2" vertical={false} />
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#7b8794', fontSize: 12 }}
            minTickGap={28}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#7b8794', fontSize: 12 }}
            tickFormatter={(value) => `${value}`}
          />
          <Tooltip
            contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 8 }}
            formatter={(value, name) => [`${value} MW`, name === 'forecast' ? 'Forecast' : 'Actual']}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
            formatter={(value) => (value === 'forecast' ? 'Forecast' : 'Actual')}
          />
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#1f7a8c"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default ForecastChart
