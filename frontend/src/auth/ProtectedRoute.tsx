import { Navigate, Outlet, useLocation } from 'react-router-dom'
import type { UserRole } from '../api/auth'
import { useAuth } from './AuthContext'

interface Props {
  roles?: UserRole[]
}

export function ProtectedRoute({ roles }: Props) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div className="screen-center">Loading…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return <Outlet />
}
