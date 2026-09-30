import { useState } from 'react'
import api, { errorMessage } from '../api/client'
import { SOURCES, STATUSES } from '../constants'
import { fromLocalInput, toLocalInput } from '../utils/dates'

export default function ApplicationForm({ initial = {}, onSaved, onClose }) {
  const isEdit = !!initial.id
  const [form, setForm] = useState({
    company: initial.company || '',
    position: initial.position || '',
    job_url: initial.job_url || '',
    location: initial.location || '',
    source: initial.source || '',
    status: initial.status || 'Saved',
    deadline: initial.deadline || '',
    follow_up_date: initial.follow_up_date || '',
    interview_date: toLocalInput(initial.interview_date),
    contact_name: initial.contact_name || '',
    contact_info: initial.contact_info || '',
    cv_version: initial.cv_version || '',
    notes: initial.notes || '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.company.trim() || !form.position.trim()) {
      setError('Company and position are required')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload = {
        ...form,
        job_url: form.job_url.trim() || null,
        location: form.location.trim() || null,
        source: form.source || null,
        deadline: form.deadline || null,
        follow_up_date: form.follow_up_date || null,
        interview_date: fromLocalInput(form.interview_date),
        contact_name: form.contact_name.trim() || null,
        contact_info: form.contact_info.trim() || null,
        cv_version: form.cv_version.trim() || null,
        notes: form.notes.trim() || null,
      }
      const res = isEdit
        ? await api.patch(`/applications/${initial.id}`, payload)
        : await api.post('/applications', payload)
      onSaved(res.data)
    } catch (err) {
      setError(errorMessage(err, 'Failed to save'))
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="drawer-form">
      <div className="drawer-body">
        {error && (
          <div className="notice notice-error" role="alert">
            {error}
          </div>
        )}

        <div className="form-row">
          <div className="field">
            <label htmlFor="input-company">Company</label>
            <input id="input-company" value={form.company} maxLength={200}
              onChange={(e) => set('company', e.target.value)} placeholder="Kaspi.kz" required />
          </div>
          <div className="field">
            <label htmlFor="input-position">Position</label>
            <input id="input-position" value={form.position} maxLength={200}
              onChange={(e) => set('position', e.target.value)} placeholder="Backend Intern" required />
          </div>
        </div>

        <div className="field">
          <label htmlFor="input-url">Job link</label>
          <input id="input-url" type="url" value={form.job_url} maxLength={500}
            onChange={(e) => set('job_url', e.target.value)} placeholder="https://" />
        </div>

        <div className="form-row">
          <div className="field">
            <label htmlFor="input-location">Location</label>
            <input id="input-location" value={form.location} maxLength={200}
              onChange={(e) => set('location', e.target.value)} placeholder="Almaty" />
          </div>
          <div className="field">
            <label htmlFor="select-source">Source</label>
            <select id="select-source" value={form.source} onChange={(e) => set('source', e.target.value)}>
              <option value="">Not set</option>
              {SOURCES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label htmlFor="select-status">Status</label>
            <select id="select-status" value={form.status} onChange={(e) => set('status', e.target.value)}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="input-cv">CV version sent</label>
            <input id="input-cv" value={form.cv_version} maxLength={200}
              onChange={(e) => set('cv_version', e.target.value)} placeholder="CV v3 (backend)" />
          </div>
        </div>

        <fieldset className="fieldset">
          <legend>Dates</legend>
          <div className="form-row">
            <div className="field">
              <label htmlFor="input-deadline">Deadline</label>
              <input id="input-deadline" type="date" value={form.deadline}
                onChange={(e) => set('deadline', e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="input-follow-up">Follow up</label>
              <input id="input-follow-up" type="date" value={form.follow_up_date}
                onChange={(e) => set('follow_up_date', e.target.value)} />
            </div>
          </div>
          <div className="field">
            <label htmlFor="input-interview">Interview (your local time)</label>
            <input id="input-interview" type="datetime-local" value={form.interview_date}
              onChange={(e) => set('interview_date', e.target.value)} />
          </div>
        </fieldset>

        <fieldset className="fieldset">
          <legend>Contact</legend>
          <div className="form-row">
            <div className="field">
              <label htmlFor="input-contact-name">Name</label>
              <input id="input-contact-name" value={form.contact_name} maxLength={200}
                onChange={(e) => set('contact_name', e.target.value)} placeholder="Recruiter" />
            </div>
            <div className="field">
              <label htmlFor="input-contact-info">Email, phone or Telegram</label>
              <input id="input-contact-info" value={form.contact_info} maxLength={300}
                onChange={(e) => set('contact_info', e.target.value)} />
            </div>
          </div>
        </fieldset>

        <div className="field">
          <label htmlFor="input-notes">Notes</label>
          <textarea id="input-notes" rows={5} value={form.notes}
            onChange={(e) => set('notes', e.target.value)}
            placeholder="Interview prep, questions to ask, next steps" />
        </div>
      </div>

      <footer className="drawer-foot">
        <button type="button" className="btn" onClick={onClose}>Cancel</button>
        <button id="btn-submit-form" type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving' : isEdit ? 'Save changes' : 'Add application'}
        </button>
      </footer>
    </form>
  )
}
