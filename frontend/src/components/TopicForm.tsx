import { useState, type FormEvent } from 'react'
import { Modal } from './Modal'

interface Props {
  heading: string
  initialTitle?: string
  onSubmit: (title: string) => Promise<void>
  onClose: () => void
}

export function TopicForm({ heading, initialTitle = '', onSubmit, onClose }: Props) {
  const [title, setTitle] = useState(initialTitle)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setPending(true)
    try {
      await onSubmit(title.trim())
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setPending(false)
    }
  }

  return (
    <Modal title={heading} onClose={onClose}>
      <form className="modal-form" onSubmit={submit}>
        <label className="field">
          <span>Topic title</span>
          <input value={title} maxLength={200} placeholder="SQL Joins" autoFocus onChange={(e) => setTitle(e.target.value)} required />
        </label>
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Cancel</button>
          <button type="submit" className="primary-button" disabled={pending || !title.trim()}>
            {pending ? 'Saving…' : 'Save'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
