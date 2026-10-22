import { KeyRound, Plus } from 'lucide-react'
import { useCallback, useState, type FormEvent } from 'react'
import type { User, UserRole } from '../api/auth'
import { listUsers, updateUser } from '../api/users'
import { useAuth } from '../auth/AuthContext'
import { Modal } from '../components/Modal'
import { UserForm } from '../components/UserForm'
import { useAsync } from '../hooks/useAsync'

const roleLabel: Record<UserRole, string> = {
  admin: 'Administrator',
  teacher: 'Teacher',
  student: 'Student',
}

function ResetPasswordDialog({ user, onClose }: { user: User; onClose: () => void }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [done, setDone] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      await updateUser(user.id, { password })
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setPending(false)
    }
  }

  return (
    <Modal title={`Reset password for ${user.full_name}`} onClose={onClose}>
      {done ? (
        <>
          <p className="modal-text">The password was updated. Share it with the user securely.</p>
          <div className="modal-actions">
            <button className="primary-button" onClick={onClose}>Done</button>
          </div>
        </>
      ) : (
        <form className="modal-form" onSubmit={submit}>
          <label className="field">
            <span>New password (min. 8 characters)</span>
            <input type="password" autoComplete="new-password" value={password} minLength={8} maxLength={128} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          {error && <div className="form-error" role="alert">{error}</div>}
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={onClose}>Cancel</button>
            <button type="submit" className="primary-button" disabled={pending || password.length < 8}>
              {pending ? 'Saving…' : 'Update password'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  )
}

export function UsersPage() {
  const { user: me } = useAuth()
  const [filter, setFilter] = useState<UserRole | ''>('')
  const fetchUsers = useCallback(() => listUsers(filter || undefined), [filter])
  const users = useAsync(fetchUsers)
  const [creating, setCreating] = useState(false)
  const [resetting, setResetting] = useState<User | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  async function toggleActive(target: User) {
    setActionError(null)
    try {
      await updateUser(target.id, { is_active: !target.is_active })
      users.reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Could not update the user.')
    }
  }

  return (
    <div className="page-wrap">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">ADMINISTRATION</p>
          <h1>Users</h1>
          <p className="welcome-subtitle">Create teacher and student accounts and manage access.</p>
        </div>
        <button className="primary-button" onClick={() => setCreating(true)}>
          <Plus size={17} /> New user
        </button>
      </section>

      <section className="panel">
        <div className="filter-row">
          <label className="field inline-field">
            <span>Role</span>
            <select value={filter} onChange={(e) => setFilter(e.target.value as UserRole | '')}>
              <option value="">All users</option>
              <option value="teacher">Teachers</option>
              <option value="student">Students</option>
              <option value="admin">Administrators</option>
            </select>
          </label>
        </div>
        {users.loading && !users.data && <p className="muted-text">Loading users…</p>}
        {users.error && <div className="form-error" role="alert">{users.error}</div>}
        {actionError && <div className="form-error" role="alert">{actionError}</div>}
        {users.data && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th aria-label="Actions" /></tr>
              </thead>
              <tbody>
                {users.data.map((u) => (
                  <tr key={u.id}>
                    <td>{u.full_name}</td>
                    <td>{u.email}</td>
                    <td>{roleLabel[u.role]}</td>
                    <td><span className={`badge ${u.is_active ? 'ok' : 'off'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td className="row-actions">
                      <button className="icon-button" aria-label={`Reset password for ${u.full_name}`} onClick={() => setResetting(u)}>
                        <KeyRound size={15} />
                      </button>
                      <button
                        className="secondary-button small"
                        onClick={() => toggleActive(u)}
                        disabled={u.id === me?.id}
                        title={u.id === me?.id ? 'You cannot deactivate yourself' : undefined}
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {creating && (
        <UserForm
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false)
            users.reload()
          }}
        />
      )}
      {resetting && <ResetPasswordDialog user={resetting} onClose={() => setResetting(null)} />}
    </div>
  )
}
