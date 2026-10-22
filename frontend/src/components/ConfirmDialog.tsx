import { useState } from 'react'
import { Modal } from './Modal'

interface Props {
  title: string
  message: string
  confirmLabel?: string
  onConfirm: () => Promise<void>
  onClose: () => void
}

export function ConfirmDialog({ title, message, confirmLabel = 'Delete', onConfirm, onClose }: Props) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function confirm() {
    setPending(true)
    setError(null)
    try {
      await onConfirm()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setPending(false)
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <p className="modal-text">{message}</p>
      {error && <div className="form-error" role="alert">{error}</div>}
      <div className="modal-actions">
        <button className="secondary-button" onClick={onClose} disabled={pending}>Cancel</button>
        <button className="danger-button" onClick={confirm} disabled={pending}>
          {pending ? 'Working…' : confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
