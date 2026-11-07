import axios from 'axios'

// `npm run dev`: Vite proxies /api → localhost:8000.
const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

const AUTH_PATHS = ['/auth/login', '/auth/register']

// An expired or invalid token logs the user out. A wrong password on the
// login form is also a 401, and must stay on the page to show its message.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const isAuthForm = AUTH_PATHS.some((p) => err.config?.url?.endsWith(p))
    if (err.response?.status === 401 && !isAuthForm) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// FastAPI returns `detail` as a string, or as a list of {loc, msg} for 422.
export function errorMessage(err, fallback = 'Something went wrong') {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((d) => {
        const field = d.loc?.[d.loc.length - 1]
        const msg = String(d.msg || '').replace(/^Value error, /, '')
        const label = field && field !== 'body' ? labelFor(field) : ''
        // "Job URL must be..." already names the field; don't repeat it.
        return label && !msg.toLowerCase().startsWith(label.toLowerCase()) ? `${label}: ${msg}` : msg
      })
      .join('. ')
  }
  if (err?.code === 'ERR_NETWORK') return 'Cannot reach the server'
  if (err?.response?.status >= 500) {
    return 'Server error — check the backend logs'
  }
  return fallback
}

function labelFor(field) {
  return String(field).replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())
}

export default api
