import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import type { User } from '../api/auth'
import { ProtectedRoute } from './ProtectedRoute'

const authState = vi.hoisted(() => ({
  user: null as User | null,
  loading: false,
}))

vi.mock('./AuthContext', () => ({
  useAuth: () => ({ ...authState, login: vi.fn(), logout: vi.fn() }),
}))

const teacher: User = {
  id: '1',
  email: 't@example.com',
  full_name: 'T',
  role: 'teacher',
  is_active: true,
  created_at: '',
}

function renderAt(path: string, roles?: User['role'][]) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/login" element={<div>login page</div>} />
        <Route path="/" element={<div>home page</div>} />
        <Route element={<ProtectedRoute roles={roles} />}>
          <Route path="/secret" element={<div>secret page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects anonymous visitors to login', () => {
    authState.user = null
    authState.loading = false
    renderAt('/secret')
    expect(screen.getByText('login page')).toBeInTheDocument()
  })

  it('shows a loading state while the session is being restored', () => {
    authState.user = null
    authState.loading = true
    renderAt('/secret')
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders the page for a signed-in user with an allowed role', () => {
    authState.user = teacher
    authState.loading = false
    renderAt('/secret', ['teacher', 'admin'])
    expect(screen.getByText('secret page')).toBeInTheDocument()
  })

  it('sends a signed-in user without the role back to the dashboard', () => {
    authState.user = teacher
    authState.loading = false
    renderAt('/secret', ['admin'])
    expect(screen.getByText('home page')).toBeInTheDocument()
  })
})
