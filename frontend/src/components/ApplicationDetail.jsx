import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../api/client'
import { STATUSES } from '../constants'
import { formatDateTime, formatDay } from '../utils/dates'
import Drawer from './Drawer'
import ApplicationForm from './ApplicationForm'

function Fact({ label, children }) {
  if (!children) return null
  return (
    <div className="fact">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  )
}

export default function ApplicationDetail({ app, onClose, onChanged, onDeleted }) {
  const [editing, setEditing] = useState(false)
  const [history, setHistory] = useState(null)
  const [busy, setBusy] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [error, setError] = useState('')

  const loadHistory = useCallback(async () => {
    try {
      const res = await api.get(`/applications/${app.id}/history`)
      setHistory(res.data)
    } catch {
      setHistory([])
    }
  }, [app.id])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  const changeStatus = async (status) => {
    if (status === app.status || busy) return
    setBusy(true)
    setError('')
    try {
      const res = await api.patch(`/applications/${app.id}`, { status })
      onChanged(res.data)
      await loadHistory()
    } catch (err) {
      setError(errorMessage(err, 'Could not change status'))
    } finally {
      setBusy(false)
    }
  }

  const handleDelete = async () => {
    setBusy(true)
    setError('')
    try {
      await api.delete(`/applications/${app.id}`)
      onDeleted(app.id)
    } catch (err) {
      setError(errorMessage(err, 'Could not delete'))
      setBusy(false)
      setConfirmDelete(false)
    }
  }

  if (editing) {
    return (
      <Drawer title="Edit application" subtitle={`${app.company} — ${app.position}`} onClose={() => setEditing(false)} id="modal-edit">
        <ApplicationForm
          initial={app}
          onClose={() => setEditing(false)}
          onSaved={(updated) => {
            onChanged(updated)
            setEditing(false)
            loadHistory()
          }}
        />
      </Drawer>
    )
  }

  return (
    <Drawer title={app.company} subtitle={app.position} onClose={onClose} id="modal-detail">
      <div className="drawer-body">
        {error && (
          <div className="notice notice-error" role="alert">
            {error}
          </div>
        )}

        <section>
          <h3 className="section-label">Status</h3>
          <div className="segmented" role="group" aria-label="Change status">
            {STATUSES.map((s) => (
              <button
                key={s}
                type="button"
                className={`segment status-${s.toLowerCase()}${app.status === s ? ' is-active' : ''}`}
                aria-pressed={app.status === s}
                disabled={busy}
                onClick={() => changeStatus(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </section>

        <dl className="facts">
          <Fact label="Location">{app.location}</Fact>
          <Fact label="Source">{app.source}</Fact>
          <Fact label="Deadline">{app.deadline && <span className="mono">{formatDay(app.deadline, true)}</span>}</Fact>
          <Fact label="Follow up">{app.follow_up_date && <span className="mono">{formatDay(app.follow_up_date, true)}</span>}</Fact>
          <Fact label="Interview">{app.interview_date && <span className="mono">{formatDateTime(app.interview_date, true)}</span>}</Fact>
          <Fact label="Contact">
            {(app.contact_name || app.contact_info) && (
              <>
                {app.contact_name}
                {app.contact_name && app.contact_info && <br />}
                {app.contact_info && <span className="muted">{app.contact_info}</span>}
              </>
            )}
          </Fact>
          <Fact label="CV version">{app.cv_version}</Fact>
          <Fact label="Job link">
            {app.job_url && (
              <a href={app.job_url} target="_blank" rel="noreferrer noopener" className="ellipsis">
                {app.job_url}
              </a>
            )}
          </Fact>
          <Fact label="Notes">{app.notes && <span className="notes">{app.notes}</span>}</Fact>
        </dl>

        <section>
          <h3 className="section-label">History</h3>
          {history === null ? (
            <p className="muted small">Loading</p>
          ) : (
            <ol className="history">
              {history.map((h) => (
                <li key={h.id}>
                  <span className="mono history-date">{formatDateTime(h.changed_at, true)}</span>
                  <span>
                    {h.old_status ? (
                      <>
                        {h.old_status} <span className="muted">to</span> <strong>{h.new_status}</strong>
                      </>
                    ) : (
                      <>
                        <span className="muted">Added as</span> <strong>{h.new_status}</strong>
                      </>
                    )}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>

      <footer className="drawer-foot">
        {confirmDelete ? (
          <>
            <span className="muted small">Delete this application and its history?</span>
            <span className="grow" />
            <button className="btn" onClick={() => setConfirmDelete(false)} disabled={busy}>Keep</button>
            <button id="btn-delete-confirm" className="btn btn-danger" onClick={handleDelete} disabled={busy}>
              Delete permanently
            </button>
          </>
        ) : (
          <>
            <button id="btn-delete" className="btn btn-quiet-danger" onClick={() => setConfirmDelete(true)} disabled={busy}>
              Delete
            </button>
            <span className="grow" />
            <button id="btn-edit" className="btn btn-primary" onClick={() => setEditing(true)} disabled={busy}>
              Edit
            </button>
          </>
        )}
      </footer>
    </Drawer>
  )
}
