import { useState, type FormEvent } from 'react'
import { useCallback } from 'react'
import { createCourse, updateCourse, type Course } from '../api/courses'
import { listUsers } from '../api/users'
import { useAuth } from '../auth/AuthContext'
import { useAsync } from '../hooks/useAsync'
import { Modal } from './Modal'

interface Props {
  course?: Course
  onSaved: (course: Course) => void
  onClose: () => void
}

export function CourseForm({ course, onSaved, onClose }: Props) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [code, setCode] = useState(course?.code ?? '')
  const [title, setTitle] = useState(course?.title ?? '')
  const [description, setDescription] = useState(course?.description ?? '')
  const [teacherId, setTeacherId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const needsTeacher = isAdmin && !course
  const fetchTeachers = useCallback(
    () => (needsTeacher ? listUsers('teacher') : Promise.resolve([])),
    [needsTeacher],
  )
  const teachers = useAsync(fetchTeachers)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setPending(true)
    try {
      const body = {
        code: code.trim(),
        title: title.trim(),
        description: description.trim() || null,
      }
      const saved = course
        ? await updateCourse(course.id, body)
        : await createCourse({ ...body, ...(needsTeacher ? { teacher_id: teacherId } : {}) })
      onSaved(saved)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setPending(false)
    }
  }

  const invalid = !code.trim() || !title.trim() || (needsTeacher && !teacherId)

  return (
    <Modal title={course ? 'Edit course' : 'New course'} onClose={onClose}>
      <form className="modal-form" onSubmit={submit}>
        {needsTeacher && (
          <label className="field">
            <span>Teacher</span>
            <select value={teacherId} onChange={(e) => setTeacherId(e.target.value)} required>
              <option value="">Select a teacher…</option>
              {(teachers.data ?? []).map((t) => (
                <option key={t.id} value={t.id}>{t.full_name} ({t.email})</option>
              ))}
            </select>
          </label>
        )}
        <label className="field">
          <span>Course code</span>
          <input value={code} maxLength={50} placeholder="CS301" onChange={(e) => setCode(e.target.value)} required />
        </label>
        <label className="field">
          <span>Title</span>
          <input value={title} maxLength={200} placeholder="Database Systems" onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label className="field">
          <span>Description (optional)</span>
          <textarea value={description} rows={3} maxLength={5000} onChange={(e) => setDescription(e.target.value)} />
        </label>
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Cancel</button>
          <button type="submit" className="primary-button" disabled={pending || invalid}>
            {pending ? 'Saving…' : 'Save course'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
