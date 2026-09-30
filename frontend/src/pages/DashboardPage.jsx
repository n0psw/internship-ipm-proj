import { useCallback, useEffect, useRef, useState } from 'react'
import api, { errorMessage } from '../api/client'
import { STATUSES } from '../constants'
import { downloadCsv } from '../utils/csv'
import { todayISO } from '../utils/dates'
import Navbar from '../components/Navbar'
import Overview from '../components/Overview'
import SearchFilter from '../components/SearchFilter'
import KanbanBoard from '../components/KanbanBoard'
import Drawer from '../components/Drawer'
import ApplicationForm from '../components/ApplicationForm'
import ApplicationDetail from '../components/ApplicationDetail'

const DEFAULT_FILTERS = {
  search: '',
  location: '',
  status: '',
  deadlineFrom: '',
  deadlineTo: '',
  sort: 'created_at',
}

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

export default function DashboardPage() {
  const [applications, setApplications] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState('')

  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const search = useDebounced(filters.search)
  const location = useDebounced(filters.location)

  const [showForm, setShowForm] = useState(false)
  const [selected, setSelected] = useState(null)

  const requestId = useRef(0)

  const fetchApplications = useCallback(async () => {
    const id = ++requestId.current
    const params = { sort: filters.sort }
    if (search.trim()) params.search = search.trim()
    if (location.trim()) params.location = location.trim()
    if (filters.status) params.status = filters.status
    if (filters.deadlineFrom) params.deadline_from = filters.deadlineFrom
    if (filters.deadlineTo) params.deadline_to = filters.deadlineTo
    try {
      const res = await api.get('/applications', { params })
      if (id === requestId.current) setApplications(res.data) // ignore out-of-order responses
    } catch (err) {
      if (id === requestId.current) setNotice(errorMessage(err, 'Could not load applications'))
    }
  }, [search, location, filters.status, filters.deadlineFrom, filters.deadlineTo, filters.sort])

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get('/dashboard/stats', { params: { today: todayISO() } })
      setStats(res.data)
    } catch (err) {
      setNotice(errorMessage(err, 'Could not load the overview'))
    }
  }, [])

  useEffect(() => {
    fetchApplications().finally(() => setLoading(false))
  }, [fetchApplications])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  const refresh = () => Promise.all([fetchApplications(), fetchStats()])

  const handleAdded = () => {
    setShowForm(false)
    refresh()
  }

  const handleChanged = (updated) => {
    setSelected(updated)
    refresh()
  }

  const handleDeleted = () => {
    setSelected(null)
    refresh()
  }

  const handleMove = async (app, status) => {
    setNotice('')
    setApplications((prev) => prev.map((a) => (a.id === app.id ? { ...a, status } : a)))
    try {
      await api.patch(`/applications/${app.id}`, { status })
      refresh()
    } catch (err) {
      setApplications((prev) => prev.map((a) => (a.id === app.id ? app : a)))
      setNotice(errorMessage(err, 'Could not move the application'))
    }
  }

  const openById = async (id) => {
    const local = applications.find((a) => a.id === id)
    if (local) return setSelected(local)
    try {
      const res = await api.get(`/applications/${id}`)
      setSelected(res.data)
    } catch (err) {
      setNotice(errorMessage(err, 'Could not open the application'))
    }
  }

  const patchFilters = (patch) => setFilters((f) => ({ ...f, ...patch }))
  const isFiltered = Object.keys(DEFAULT_FILTERS).some(
    (k) => k !== 'sort' && filters[k] !== DEFAULT_FILTERS[k]
  )

  const total = stats?.total ?? applications.length
  const isEmpty = !loading && stats?.total === 0

  return (
    <div className="app-shell">
      <Navbar onAddClick={() => setShowForm(true)} />

      <main className="page">
        {notice && (
          <div className="notice notice-error" role="alert">
            <span>{notice}</span>
            <button className="link-btn" onClick={() => setNotice('')}>Dismiss</button>
          </div>
        )}

        {loading ? (
          <p className="muted" aria-live="polite">Loading</p>
        ) : isEmpty ? (
          <section className="empty">
            <h1>Nothing tracked yet</h1>
            <p className="muted">
              Save a vacancy, set its deadline, and move it across the board as things happen.
            </p>
            <button className="btn btn-primary" onClick={() => setShowForm(true)}>
              Add your first application
            </button>
          </section>
        ) : (
          <>
            <Overview stats={stats} onOpen={openById} />
            <SearchFilter
              filters={filters}
              onChange={patchFilters}
              onReset={() => setFilters((f) => ({ ...DEFAULT_FILTERS, sort: f.sort }))}
              onExport={() => downloadCsv(applications)}
              isFiltered={isFiltered}
              shown={applications.length}
              total={total}
            />
            <KanbanBoard
              applications={applications}
              statuses={filters.status ? [filters.status] : STATUSES}
              onCardClick={setSelected}
              onMove={handleMove}
            />
          </>
        )}
      </main>

      {showForm && (
        <Drawer title="New application" onClose={() => setShowForm(false)} id="modal-add">
          <ApplicationForm onSaved={handleAdded} onClose={() => setShowForm(false)} />
        </Drawer>
      )}

      {selected && (
        <ApplicationDetail
          key={selected.id}
          app={selected}
          onClose={() => setSelected(null)}
          onChanged={handleChanged}
          onDeleted={handleDeleted}
        />
      )}
    </div>
  )
}
