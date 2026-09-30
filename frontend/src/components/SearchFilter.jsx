import { SORT_OPTIONS, STATUSES } from '../constants'

export default function SearchFilter({ filters, onChange, onReset, onExport, isFiltered, shown, total }) {
  return (
    <form className="filters" id="filter-bar" onSubmit={(e) => e.preventDefault()} role="search">
      <div className="field field-search">
        <label htmlFor="input-search">Search</label>
        <input
          id="input-search"
          type="search"
          placeholder="Company or position"
          value={filters.search}
          onChange={(e) => onChange({ search: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="input-location">Location</label>
        <input
          id="input-location"
          type="text"
          placeholder="Any"
          value={filters.location}
          onChange={(e) => onChange({ location: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="select-status-filter">Status</label>
        <select
          id="select-status-filter"
          value={filters.status}
          onChange={(e) => onChange({ status: e.target.value })}
        >
          <option value="">All</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="input-deadline-from">Deadline from</label>
        <input
          id="input-deadline-from"
          type="date"
          value={filters.deadlineFrom}
          onChange={(e) => onChange({ deadlineFrom: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="input-deadline-to">Deadline to</label>
        <input
          id="input-deadline-to"
          type="date"
          value={filters.deadlineTo}
          onChange={(e) => onChange({ deadlineTo: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="select-sort">Sort</label>
        <select id="select-sort" value={filters.sort} onChange={(e) => onChange({ sort: e.target.value })}>
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      <div className="filters-foot">
        <span className="muted small" aria-live="polite">
          {isFiltered ? `Showing ${shown} of ${total}` : `${total} ${total === 1 ? 'application' : 'applications'}`}
        </span>
        {isFiltered && (
          <button type="button" className="link-btn" id="btn-reset-filters" onClick={onReset}>
            Clear filters
          </button>
        )}
        <span className="grow" />
        <button type="button" className="link-btn" id="btn-export" onClick={onExport} disabled={shown === 0}>
          Export CSV
        </button>
      </div>
    </form>
  )
}
