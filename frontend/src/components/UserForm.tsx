import { useState, type FormEvent } from 'react'
import type { User, UserRole } from '../api/auth'
import { createUser } from '../api/users'
import { Modal } from './Modal'

interface Props {
  onSaved: (user: User) => void
  onClose: () => void
  /** Roles the signed-in user may create. Teachers get only "student". */
  roles?: UserRole[]
  title?: string
}

const roleNames: Record<UserRole, string> = {
  teacher: 'Teacher',
  student: 'Student',
  admin: 'Administrator',
}

export function UserForm({
  onSaved,
  onClose,
  roles = ['teacher', 'student', 'admin'],
  title = 'New user',
}: Props) {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>(roles[0])
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setPending(true)
    try {
      onSaved(await createUser({ full_name: fullName.trim(), email: email.trim(), password, role }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setPending(false)
    }
  }

  const invalid = !fullName.trim() || !email.trim() || password.length < 8

  return (
    <Modal title={title} onClose={onClose}>
      <form className="modal-form" onSubmit={submit}>
        <label className="field">
          <span>Full name</span>
          <input value={fullName} maxLength={255} onChange={(e) => setFullName(e.target.value)} required />
        </label>
        <label className="field">
          <span>Email</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label className="field">
          <span>Temporary password (min. 8 characters)</span>
          <input type="password" autoComplete="new-password" value={password} minLength={8} maxLength={128} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        <label className="field">
          <span>Role</span>
          <select value={role} onChange={(e) => setRole(e.target.value as UserRole)} disabled={roles.length === 1}>
            {roles.map((r) => (
              <option key={r} value={r}>{roleNames[r]}</option>
            ))}
          </select>
        </label>
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Cancel</button>
          <button type="submit" className="primary-button" disabled={pending || invalid}>
            {pending ? 'Creating…' : 'Create user'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
