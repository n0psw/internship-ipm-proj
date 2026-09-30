import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }))
  const isRegister = mode === 'register'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isRegister) await register(form.name, form.email, form.password)
      else await login(form.email, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(errorMessage(err))
      setLoading(false)
    }
  }

  const toggle = () => {
    setMode(isRegister ? 'login' : 'register')
    setError('')
  }

  return (
    <main className="auth">
      <div className="auth-panel">
        <p className="wordmark">Internship Tracker</p>
        <h1>{isRegister ? 'Create an account' : 'Sign in'}</h1>
        <p className="muted">
          Every application, deadline and interview in one place.
        </p>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="notice notice-error" role="alert">
              {error}
            </div>
          )}

          {isRegister && (
            <div className="field">
              <label htmlFor="input-name">Name</label>
              <input id="input-name" type="text" autoComplete="name" required maxLength={100}
                value={form.name} onChange={(e) => set('name', e.target.value)} />
            </div>
          )}

          <div className="field">
            <label htmlFor="input-email">Email</label>
            <input id="input-email" type="email" autoComplete="email" required
              value={form.email} onChange={(e) => set('email', e.target.value)} />
          </div>

          <div className="field">
            <label htmlFor="input-password">Password</label>
            <input id="input-password" type="password" required
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              minLength={isRegister ? 8 : undefined}
              value={form.password} onChange={(e) => set('password', e.target.value)} />
            {isRegister && <span className="hint">At least 8 characters</span>}
          </div>

          <button id="btn-submit-auth" type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Please wait' : isRegister ? 'Create account' : 'Sign in'}
          </button>
        </form>

        <p className="auth-switch">
          {isRegister ? 'Already have an account?' : 'New here?'}{' '}
          <button id="btn-toggle-auth" className="link-btn" onClick={toggle}>
            {isRegister ? 'Sign in' : 'Create an account'}
          </button>
        </p>
      </div>
    </main>
  )
}
