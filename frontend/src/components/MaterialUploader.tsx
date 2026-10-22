import { UploadCloud } from 'lucide-react'
import { useRef, useState, type DragEvent } from 'react'
import { MAX_UPLOAD_MB, uploadMaterial, validateFile } from '../api/materials'

interface Props {
  courseId: string
  topicId: string
  onUploaded: () => void
}

export function MaterialUploader({ courseId, topicId, onUploaded }: Props) {
  const input = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState<number | null>(null)
  const [fileName, setFileName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  async function handleFile(file: File | undefined) {
    if (!file || progress !== null) return
    setError(null)
    setNotice(null)
    const problem = validateFile(file)
    if (problem) return setError(problem)

    setFileName(file.name)
    setProgress(0)
    try {
      await uploadMaterial(courseId, topicId, file, setProgress)
      setNotice(`Uploaded ${file.name}.`)
      onUploaded()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setProgress(null)
      if (input.current) input.current.value = ''
    }
  }

  function onDrop(event: DragEvent) {
    event.preventDefault()
    setDragging(false)
    void handleFile(event.dataTransfer.files[0])
  }

  const busy = progress !== null

  return (
    <div>
      <div
        className={`dropzone${dragging ? ' dragging' : ''}${busy ? ' busy' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <UploadCloud size={26} />
        {busy ? (
          <>
            <strong>Uploading {fileName}…</strong>
            <div className="progress-track" role="progressbar" aria-valuenow={Math.round((progress ?? 0) * 100)} aria-valuemin={0} aria-valuemax={100}>
              <span style={{ width: `${Math.round((progress ?? 0) * 100)}%` }} />
            </div>
          </>
        ) : (
          <>
            <strong>Drag a file here, or</strong>
            <button className="secondary-button" onClick={() => input.current?.click()}>Choose file</button>
            <small>PDF, PPTX or DOCX, up to {MAX_UPLOAD_MB} MB</small>
          </>
        )}
        <input
          ref={input}
          type="file"
          hidden
          accept=".pdf,.pptx,.docx"
          aria-label="Upload material"
          onChange={(e) => void handleFile(e.target.files?.[0])}
        />
      </div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {notice && <div className="form-notice" role="status">{notice}</div>}
    </div>
  )
}
