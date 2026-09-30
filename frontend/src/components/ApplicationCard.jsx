import { CLOSED_STATUSES } from '../constants'
import { formatDateTime, formatDay, isPastDay } from '../utils/dates'

function Line({ label, children, alert }) {
  return (
    <div className={`card-line${alert ? ' is-alert' : ''}`}>
      <span className="card-line-label">{label}</span>
      <span className="mono">{children}</span>
    </div>
  )
}

export default function ApplicationCard({ app, onClick, onDragStart, onDragEnd, dragging }) {
  const open = !CLOSED_STATUSES.includes(app.status)
  const deadlineOverdue = open && isPastDay(app.deadline)
  const followUpOverdue = open && isPastDay(app.follow_up_date)

  return (
    <article
      className={`card${dragging ? ' is-dragging' : ''}`}
      draggable
      onDragStart={(e) => onDragStart(e, app)}
      onDragEnd={onDragEnd}
      onClick={() => onClick(app)}
      onKeyDown={(e) => e.key === 'Enter' && onClick(app)}
      role="button"
      tabIndex={0}
      aria-label={`${app.company}, ${app.position}, ${app.status}`}
    >
      <h3 className="card-company">{app.company}</h3>
      <p className="card-position">{app.position}</p>
      {(app.location || app.deadline || app.follow_up_date || app.interview_date) && (
        <div className="card-meta">
          {app.location && <Line label="Location">{app.location}</Line>}
          {app.interview_date && <Line label="Interview">{formatDateTime(app.interview_date)}</Line>}
          {app.deadline && (
            <Line label="Deadline" alert={deadlineOverdue}>
              {formatDay(app.deadline)}
              {deadlineOverdue && ' (overdue)'}
            </Line>
          )}
          {app.follow_up_date && (
            <Line label="Follow up" alert={followUpOverdue}>
              {formatDay(app.follow_up_date)}
              {followUpOverdue && ' (overdue)'}
            </Line>
          )}
        </div>
      )}
    </article>
  )
}
