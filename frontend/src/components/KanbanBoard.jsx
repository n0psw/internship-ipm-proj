import { useState } from 'react'
import { STATUSES } from '../constants'
import ApplicationCard from './ApplicationCard'

export default function KanbanBoard({ applications, statuses = STATUSES, onCardClick, onMove }) {
  const [draggingId, setDraggingId] = useState(null)
  const [overStatus, setOverStatus] = useState(null)

  const handleDragStart = (e, app) => {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(app.id))
    setDraggingId(app.id)
  }

  const endDrag = () => {
    setDraggingId(null)
    setOverStatus(null)
  }

  const handleDrop = (e, status) => {
    e.preventDefault()
    const id = Number(e.dataTransfer.getData('text/plain'))
    const app = applications.find((a) => a.id === id)
    endDrag()
    if (app && app.status !== status) onMove(app, status)
  }

  return (
    <div className="board" id="kanban-board" style={{ '--cols': statuses.length }}>
      {statuses.map((status) => {
        const items = applications.filter((a) => a.status === status)
        return (
          <section
            key={status}
            id={`kanban-col-${status.toLowerCase()}`}
            className={`column status-${status.toLowerCase()}${overStatus === status ? ' is-over' : ''}`}
            aria-label={status}
            onDragOver={(e) => {
              e.preventDefault()
              if (overStatus !== status) setOverStatus(status)
            }}
            onDragLeave={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) setOverStatus(null)
            }}
            onDrop={(e) => handleDrop(e, status)}
          >
            <header className="column-head">
              <h2>{status}</h2>
              <span className="mono column-count">{items.length}</span>
            </header>
            <div className="column-body">
              {items.length === 0 ? (
                <p className="column-empty">None</p>
              ) : (
                items.map((app) => (
                  <ApplicationCard
                    key={app.id}
                    app={app}
                    onClick={onCardClick}
                    onDragStart={handleDragStart}
                    onDragEnd={endDrag}
                    dragging={draggingId === app.id}
                  />
                ))
              )}
            </div>
          </section>
        )
      })}
    </div>
  )
}
