import { createContext, useContext, useState, useCallback } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
  })

  const login = useCallback(async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    const { access_token, user: u } = res.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(u))
    setUser(u)
    return u
  }, [])

  const register = useCallback(async (name, email, password) => {
    const res = await api.post('/auth/register', { name, email, password })
    const { access_token, user: u } = res.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(u))
    setUser(u)
    return u
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
