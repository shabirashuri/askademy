import { BookOpen, Plus } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listCourses } from '../api/courses'
import { useAuth } from '../auth/AuthContext'
import { CourseForm } from '../components/CourseForm'
import { useAsync } from '../hooks/useAsync'

export function CoursesPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const fetchCourses = useCallback(() => listCourses(), [])
  const { data: courses, loading, error } = useAsync(fetchCourses)
  const [creating, setCreating] = useState(false)
  const canCreate = user?.role === 'teacher' || user?.role === 'admin'

  return (
    <div className="page-wrap">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">COURSES</p>
          <h1>{user?.role === 'student' ? 'My courses' : 'Courses & topics'}</h1>
          <p className="welcome-subtitle">
            {user?.role === 'student'
              ? 'Courses you are enrolled in.'
              : 'Organize your teaching into courses and topics.'}
          </p>
        </div>
        {canCreate && (
          <button className="primary-button" onClick={() => setCreating(true)}>
            <Plus size={17} /> New course
          </button>
        )}
      </section>

      {loading && <p className="muted-text">Loading courses…</p>}
      {error && <div className="form-error" role="alert">{error}</div>}
      {courses && courses.length === 0 && (
        <div className="empty-state">
          <BookOpen size={28} />
          <h3>No courses yet</h3>
          <p>
            {canCreate
              ? 'Create your first course to start adding topics and materials.'
              : 'Your teacher has not enrolled you in a course yet.'}
          </p>
        </div>
      )}
      {courses && courses.length > 0 && (
        <div className="course-grid">
          {courses.map((course) => (
            <Link className="course-card" key={course.id} to={`/courses/${course.id}`}>
              <span className="course-code">{course.code}</span>
              <h3>{course.title}</h3>
              <p>{course.description || 'No description'}</p>
            </Link>
          ))}
        </div>
      )}

      {creating && (
        <CourseForm
          onClose={() => setCreating(false)}
          onSaved={(course) => navigate(`/courses/${course.id}`)}
        />
      )}
    </div>
  )
}
