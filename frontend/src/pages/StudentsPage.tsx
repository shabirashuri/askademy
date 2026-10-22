import { Plus, Users } from 'lucide-react'
import { useCallback, useState } from 'react'
import { listUsers } from '../api/users'
import { UserForm } from '../components/UserForm'
import { useAsync } from '../hooks/useAsync'

export function StudentsPage() {
  const fetchStudents = useCallback(() => listUsers('student'), [])
  const students = useAsync(fetchStudents)
  const [adding, setAdding] = useState(false)

  return (
    <div className="page-wrap">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">STUDENTS</p>
          <h1>Students</h1>
          <p className="welcome-subtitle">
            Add student accounts, then enroll them in your courses from each course page.
          </p>
        </div>
        <button className="primary-button" onClick={() => setAdding(true)}>
          <Plus size={17} /> Add student
        </button>
      </section>

      <section className="panel">
        {students.loading && !students.data && <p className="muted-text">Loading students…</p>}
        {students.error && <div className="form-error" role="alert">{students.error}</div>}
        {students.data && students.data.length === 0 && (
          <div className="empty-state">
            <Users size={28} />
            <h3>No students yet</h3>
            <p>Add a student account to get started.</p>
          </div>
        )}
        {students.data && students.data.length > 0 && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr><th>Name</th><th>Email</th><th>Status</th></tr>
              </thead>
              <tbody>
                {students.data.map((s) => (
                  <tr key={s.id}>
                    <td>{s.full_name}</td>
                    <td>{s.email}</td>
                    <td><span className={`badge ${s.is_active ? 'ok' : 'off'}`}>{s.is_active ? 'Active' : 'Inactive'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {adding && (
        <UserForm
          title="Add student"
          roles={['student']}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false)
            students.reload()
          }}
        />
      )}
    </div>
  )
}
