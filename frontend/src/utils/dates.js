// The API sends date-only fields as "YYYY-MM-DD" and timestamps as UTC ISO
// strings ending in "Z". Dates are parsed as local calendar days (not UTC
// midnight) and timestamps are shown in the viewer's own time zone.

const pad = (n) => String(n).padStart(2, '0')

export function parseDay(str) {
  if (!str) return null
  const [y, m, d] = str.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function todayISO() {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function isPastDay(str) {
  const d = parseDay(str)
  return !!d && d < parseDay(todayISO())
}

export function formatDay(str, withYear = false) {
  const d = parseDay(str)
  if (!d) return ''
  return d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    ...(withYear ? { year: 'numeric' } : {}),
  })
}

export function formatDateTime(iso, withYear = false) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    ...(withYear ? { year: 'numeric' } : {}),
    hour: '2-digit',
    minute: '2-digit',
  })
}

// <input type="datetime-local"> works in local time with no zone attached.
export function toLocalInput(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function fromLocalInput(value) {
  return value ? new Date(value).toISOString() : null
}
