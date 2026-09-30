import { formatDateTime, formatDay } from '../utils/dates'

const KIND_LABEL = { deadline: 'Deadline', follow_up: 'Follow up', interview: 'Interview' }
const MAX_ROWS = 6

function Metric({ label, value, hint }) {
  return (
    <div className="metric">
      <dt>{label}</dt>
      <dd>{value}</dd>
      {hint && <span className="metric-hint">{hint}</span>}
    </div>
  )
}

export default function Overview({ stats, onOpen }) {
  if (!stats) return <section className="overview" aria-busy="true" />

  const upcoming = stats.upcoming
  const shown = upcoming.slice(0, MAX_ROWS)
  const rate = stats.response_rate

  return (
    <section className="overview" aria-label="Overview">
      <dl className="metrics" id="stats-row">
        <Metric label="Tracked" value={stats.total} />
        <Metric label="Submitted" value={stats.submitted} />
        <Metric
          label="Response rate"
          value={rate == null ? '—' : `${rate}%`}
          hint={rate == null ? 'Nothing submitted yet' : 'Reached interview or offer'}
        />
      </dl>

      <div className="agenda">
        <h2 className="section-label">Next 7 days</h2>
        {shown.length === 0 ? (
          <p className="muted">Nothing due. Deadlines, follow-ups and interviews appear here.</p>
        ) : (
          <ul className="agenda-list">
            {shown.map((item) => (
              <li key={`${item.kind}-${item.application_id}`}>
                <button className="agenda-row" onClick={() => onOpen(item.application_id)}>
                  <span className="agenda-when mono">
                    {item.kind === 'interview' ? formatDateTime(item.when) : formatDay(item.when)}
                  </span>
                  <span className="agenda-what">
                    <strong>{item.company}</strong>
                    <span className="muted"> {KIND_LABEL[item.kind]}</span>
                  </span>
                  {item.overdue && <span className="flag">Overdue</span>}
                </button>
              </li>
            ))}
          </ul>
        )}
        {upcoming.length > MAX_ROWS && (
          <p className="muted small">and {upcoming.length - MAX_ROWS} more</p>
        )}
      </div>
    </section>
  )
}
