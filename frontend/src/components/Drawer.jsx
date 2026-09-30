import { useEffect, useRef } from 'react'

const FOCUSABLE = 'input, select, textarea, button:not([disabled]), a[href]'

export default function Drawer({ title, subtitle, onClose, children, id }) {
  const panelRef = useRef(null)

  useEffect(() => {
    const previous = document.activeElement
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'Tab') {
        const nodes = panelRef.current?.querySelectorAll(FOCUSABLE)
        if (!nodes?.length) return
        const first = nodes[0]
        const last = nodes[nodes.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    panelRef.current?.querySelector('input, select, textarea')?.focus()
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      previous?.focus?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="scrim" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside className="drawer" id={id} role="dialog" aria-modal="true" aria-label={title} ref={panelRef}>
        <header className="drawer-head">
          <div className="drawer-titles">
            <h2 className="drawer-title">{title}</h2>
            {subtitle && <p className="drawer-subtitle">{subtitle}</p>}
          </div>
          <button className="link-btn" onClick={onClose} aria-label="Close">
            Close
          </button>
        </header>
        {children}
      </aside>
    </div>
  )
}
