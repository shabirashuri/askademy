import { UserMinus, UserPlus } from 'lucide-react'
import { useCallback, useState } from 'react'
import {
  enrollStudent,
  listEnrollments,
  unenrollStudent,
  type Enrollment,
} from '../api/courses'
import { listUsers } from '../api/users'
import { useAsync } from '../hooks/useAsync'
import { ConfirmDialog } from './ConfirmDialog'

export function EnrollmentPanel({ courseId }: { courseId: string }) {
  const fetchEnrollments = useCallback(() => listEnrollments(courseId), [courseId])
  const fetchStudents = useCallback(() => listUsers('student'), [])
  const enrollments = useAsync(fetchEnrollments)
  const students = useAsync(fetchStudents)

  const [selected, setSelected] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<Enrollment | null>(null)

  const enrolledIds = new Set((enrollments.data ?? []).map((e) => e.student_id))
  const available = (students.data ?? []).filter((s) => s.is_active && !enrolledIds.has(s.id))

  async function add() {
    if (!selected) return
    setPending(true)
    setError(null)
    try {
      await enrollStudent(courseId, selected)
      setSelected('')
      enrollments.reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not enroll the student.')
    } finally {
      setPending(false)
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">CLASS LIST</p>
          <h3>Students</h3>
        </div>
        <span className="step-count">{enrollments.data?.length ?? 0} enrolled</span>
      </div>

      <div className="enroll-row">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          aria-label="Student to enroll"
          disabled={available.length === 0}
        >
          <option value="">
            {available.length === 0 ? 'No students available to enroll' : 'Select a student…'}
          </option>
          {available.map((s) => (
            <option key={s.id} value={s.id}>{s.full_name} ({s.email})</option>
          ))}
        </select>
        <button className="primary-button" onClick={add} disabled={!selected || pending}>
          <UserPlus size={16} /> {pending ? 'Enrolling…' : 'Enroll'}
        </button>
      </div>

      {error && <div className="form-error" role="alert">{error}</div>}
      {(enrollments.error || students.error) && (
        <div className="form-error" role="alert">{enrollments.error ?? students.error}</div>
      )}
      {enrollments.data && enrollments.data.length === 0 && (
        <p className="muted-text">No students are enrolled yet.</p>
      )}
      <ul className="people-list">
        {(enrollments.data ?? []).map((e) => (
          <li key={e.id}>
            <div>
              <strong>{e.student.full_name}</strong>
              <span>{e.student.email}</span>
            </div>
            <button
              className="icon-button"
              aria-label={`Remove ${e.student.full_name}`}
              onClick={() => setRemoving(e)}
            >
              <UserMinus size={15} />
            </button>
          </li>
        ))}
      </ul>

      {removing && (
        <ConfirmDialog
          title="Remove student"
          message={`Remove ${removing.student.full_name} from this course? They will lose access to it.`}
          confirmLabel="Remove"
          onClose={() => setRemoving(null)}
          onConfirm={async () => {
            await unenrollStudent(courseId, removing.student_id)
            enrollments.reload()
          }}
        />
      )}
    </section>
  )
}
