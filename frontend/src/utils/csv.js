const COLUMNS = [
  ['company', 'Company'],
  ['position', 'Position'],
  ['status', 'Status'],
  ['location', 'Location'],
  ['source', 'Source'],
  ['job_url', 'Job URL'],
  ['deadline', 'Deadline'],
  ['follow_up_date', 'Follow-up date'],
  ['interview_date', 'Interview (UTC)'],
  ['contact_name', 'Contact'],
  ['contact_info', 'Contact details'],
  ['cv_version', 'CV version'],
  ['notes', 'Notes'],
  ['created_at', 'Added (UTC)'],
]

function cell(value) {
  let s = value == null ? '' : String(value)
  // Spreadsheets run cells that start with these characters as formulas.
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`
  return `"${s.replace(/"/g, '""')}"`
}

export function applicationsToCsv(applications) {
  const header = COLUMNS.map(([, label]) => cell(label)).join(',')
  const rows = applications.map((a) => COLUMNS.map(([key]) => cell(a[key])).join(','))
  return [header, ...rows].join('\r\n')
}

export function downloadCsv(applications) {
  // BOM so Excel reads the file as UTF-8.
  const blob = new Blob(['﻿' + applicationsToCsv(applications)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `internship-applications-${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
