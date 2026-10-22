import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export function LoginPage() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  if (loading) return <div className="screen-center">Loading…</div>
  if (user) return <Navigate to={from} replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setPending(true)
    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Try again.')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="screen-center login-screen">
      <form className="login-card" onSubmit={handleSubmit} noValidate>
        <div className="brand login-brand">
          <span className="brand-mark">S</span>
          <span>
            <strong>smartbank</strong>
            <small>LEARNING PLATFORM</small>
          </span>
        </div>
        <h1>Welcome back</h1>
        <p className="login-subtitle">Log in to your teaching workspace.</p>

        <label className="field">
          <span>Email</span>
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}

        <button className="primary-button login-submit" type="submit" disabled={pending || !email || !password}>
          {pending ? 'Logging in…' : 'Log in'}
        </button>
        <p className="login-hint">Accounts are created by your administrator.</p>
      </form>
    </div>
  )
}
