
const API_BASE_URL = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000'
).replace(/\/+$/, '')

export async function fetchAnalysis({
  start = '2026-01-01',
  end = '2026-02-01',
  cutoffHour = 10,
} = {}) {
  if (!start || !end || start >= end) {
    throw new Error('Start date must be earlier than end date.')
  }

  const params = new URLSearchParams({
    start,
    end,
    cutoff_hour: String(cutoffHour),
  })

  let response

  try {
    response = await fetch(
      `${API_BASE_URL}/api/analysis?${params.toString()}`,
    )
  } catch {
    throw new Error(
      'Cannot connect to the WindWise API. Check that the backend is running.',
    )
  }

  let payload

  try {
    payload = await response.json()
  } catch {
    throw new Error(
      `The API returned an invalid response (HTTP ${response.status}).`,
    )
  }

  if (!response.ok) {
    throw new Error(
      payload?.detail || `Unable to load analysis (HTTP ${response.status}).`,
    )
  }

  return payload
}
