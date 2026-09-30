import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar({ onAddClick }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <span className="wordmark">Internship Tracker</span>
        <div className="topbar-right">
          <span className="topbar-user">{user?.name}</span>
          <button id="btn-logout" className="link-btn" onClick={handleLogout}>
            Sign out
          </button>
          <button id="btn-add-application" className="btn btn-primary" onClick={onAddClick}>
            New application
          </button>
        </div>
      </div>
    </header>
  )
}
