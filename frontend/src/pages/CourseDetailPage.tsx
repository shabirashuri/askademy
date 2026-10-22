import { ArrowLeft, Pencil, Plus, Trash2 } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  createTopic,
  deleteCourse,
  deleteTopic,
  getCourse,
  listTopics,
  renameTopic,
  reorderTopics,
  type Topic,
} from '../api/courses'
import { useAuth } from '../auth/AuthContext'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { CourseForm } from '../components/CourseForm'
import { EnrollmentPanel } from '../components/EnrollmentPanel'
import { MaterialList } from '../components/MaterialList'
import { TopicForm } from '../components/TopicForm'
import { TopicTree } from '../components/TopicTree'
import { childrenOf } from '../components/topicUtils'
import { useAsync } from '../hooks/useAsync'

type Dialog =
  | { kind: 'add'; parent: Topic | null }
  | { kind: 'rename'; topic: Topic }
  | { kind: 'delete-topic'; topic: Topic }
  | { kind: 'edit-course' }
  | { kind: 'delete-course' }
  | null

export function CourseDetailPage() {
  const { id = '' } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const canEdit = user?.role === 'teacher' || user?.role === 'admin'

  const fetchCourse = useCallback(() => getCourse(id), [id])
  const fetchTopics = useCallback(() => listTopics(id), [id])
  const course = useAsync(fetchCourse)
  const topics = useAsync(fetchTopics)
  const [dialog, setDialog] = useState<Dialog>(null)
  const [moveError, setMoveError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selectedTopic = (topics.data ?? []).find((t) => t.id === selectedId) ?? null

  async function move(topic: Topic, direction: -1 | 1) {
    const siblings = childrenOf(topics.data ?? [], topic.parent_topic_id)
    const from = siblings.findIndex((t) => t.id === topic.id)
    const to = from + direction
    if (to < 0 || to >= siblings.length) return
    ;[siblings[from], siblings[to]] = [siblings[to], siblings[from]]
    try {
      setMoveError(null)
      await reorderTopics(id, siblings.map((t, position) => ({ id: t.id, position })))
      topics.reload()
    } catch (err) {
      setMoveError(err instanceof Error ? err.message : 'Could not reorder topics.')
    }
  }

  if (course.loading) return <div className="page-wrap"><p className="muted-text">Loading…</p></div>
  if (course.error || !course.data) {
    return (
      <div className="page-wrap">
        <Link className="back-link" to="/courses"><ArrowLeft size={15} /> Back to courses</Link>
        <div className="form-error" role="alert">{course.error ?? 'Course not found.'}</div>
      </div>
    )
  }
  const c = course.data

  return (
    <div className="page-wrap">
      <Link className="back-link" to="/courses"><ArrowLeft size={15} /> Back to courses</Link>
      <section className="welcome-row">
        <div>
          <p className="eyebrow">{c.code}</p>
          <h1>{c.title}</h1>
          {c.description && <p className="welcome-subtitle">{c.description}</p>}
        </div>
        {canEdit && (
          <div className="button-row">
            <button className="secondary-button" onClick={() => setDialog({ kind: 'edit-course' })}>
              <Pencil size={15} /> Edit
            </button>
            <button className="danger-button" onClick={() => setDialog({ kind: 'delete-course' })}>
              <Trash2 size={15} /> Delete
            </button>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">STRUCTURE</p>
            <h3>Topics</h3>
          </div>
          {canEdit && (
            <button className="primary-button" onClick={() => setDialog({ kind: 'add', parent: null })}>
              <Plus size={16} /> Add topic
            </button>
          )}
        </div>
        {topics.loading && !topics.data && <p className="muted-text">Loading topics…</p>}
        {topics.error && <div className="form-error" role="alert">{topics.error}</div>}
        {moveError && <div className="form-error" role="alert">{moveError}</div>}
        {topics.data && (
          <TopicTree
            topics={topics.data}
            canEdit={canEdit}
            selectedId={selectedTopic?.id}
            onSelect={canEdit ? (topic) => setSelectedId(topic.id) : undefined}
            onAdd={(parent) => setDialog({ kind: 'add', parent })}
            onRename={(topic) => setDialog({ kind: 'rename', topic })}
            onDelete={(topic) => setDialog({ kind: 'delete-topic', topic })}
            onMove={move}
          />
        )}
      </section>

      {canEdit && (
        selectedTopic ? (
          <MaterialList
            key={selectedTopic.id}
            courseId={id}
            topicId={selectedTopic.id}
            topicTitle={selectedTopic.title}
          />
        ) : (
          <section className="panel">
            <p className="muted-text">Select a topic above to upload and manage its learning material.</p>
          </section>
        )
      )}

      {canEdit && <EnrollmentPanel courseId={id} />}

      {dialog?.kind === 'add' && (
        <TopicForm
          heading={dialog.parent ? `New sub-topic of “${dialog.parent.title}”` : 'New topic'}
          onClose={() => setDialog(null)}
          onSubmit={async (title) => {
            await createTopic(id, title, dialog.parent?.id ?? null)
            topics.reload()
          }}
        />
      )}
      {dialog?.kind === 'rename' && (
        <TopicForm
          heading="Rename topic"
          initialTitle={dialog.topic.title}
          onClose={() => setDialog(null)}
          onSubmit={async (title) => {
            await renameTopic(dialog.topic.id, title)
            topics.reload()
          }}
        />
      )}
      {dialog?.kind === 'delete-topic' && (
        <ConfirmDialog
          title="Delete topic"
          message={`Delete “${dialog.topic.title}” and all of its sub-topics? Materials attached to them will be removed too.`}
          onClose={() => setDialog(null)}
          onConfirm={async () => {
            await deleteTopic(dialog.topic.id)
            topics.reload()
          }}
        />
      )}
      {dialog?.kind === 'edit-course' && (
        <CourseForm
          course={c}
          onClose={() => setDialog(null)}
          onSaved={() => {
            setDialog(null)
            course.reload()
          }}
        />
      )}
      {dialog?.kind === 'delete-course' && (
        <ConfirmDialog
          title="Delete course"
          message={`Delete “${c.title}” with all of its topics and materials? This cannot be undone from the app.`}
          onClose={() => setDialog(null)}
          onConfirm={async () => {
            await deleteCourse(c.id)
            navigate('/courses', { replace: true })
          }}
        />
      )}
    </div>
  )
}
