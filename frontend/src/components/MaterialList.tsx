import { Download, FileText, Trash2 } from 'lucide-react'
import { useCallback, useState } from 'react'
import { deleteMaterial, listMaterials, saveMaterial, type Material } from '../api/materials'
import { useAsync } from '../hooks/useAsync'
import { ConfirmDialog } from './ConfirmDialog'
import { MaterialUploader } from './MaterialUploader'

interface Props {
  courseId: string
  topicId: string
  topicTitle: string
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const statusLabel: Record<Material['status'], string> = {
  uploaded: 'Uploaded',
  extracting: 'Processing',
  ready: 'Ready',
  failed: 'Failed',
}

export function MaterialList({ courseId, topicId, topicTitle }: Props) {
  const fetchMaterials = useCallback(() => listMaterials(courseId, topicId), [courseId, topicId])
  const materials = useAsync(fetchMaterials)
  const [removing, setRemoving] = useState<Material | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function download(material: Material) {
    setError(null)
    try {
      await saveMaterial(material)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed.')
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">LEARNING MATERIAL</p>
          <h3>{topicTitle}</h3>
        </div>
        <span className="step-count">{materials.data?.length ?? 0} files</span>
      </div>

      <MaterialUploader courseId={courseId} topicId={topicId} onUploaded={materials.reload} />

      {materials.error && <div className="form-error" role="alert">{materials.error}</div>}
      {error && <div className="form-error" role="alert">{error}</div>}
      {materials.data && materials.data.length === 0 && (
        <p className="muted-text material-empty">No material uploaded for this topic yet.</p>
      )}
      <ul className="people-list">
        {(materials.data ?? []).map((m) => (
          <li key={m.id}>
            <div className="file-info">
              <FileText size={18} />
              <div>
                <strong>{m.file_name}</strong>
                <span>
                  {m.file_type.toUpperCase()} · {formatSize(m.file_size_bytes)} ·{' '}
                  {new Date(m.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            <div className="row-actions">
              <span className={`badge ${m.status === 'failed' ? 'off' : 'ok'}`}>{statusLabel[m.status]}</span>
              <button className="icon-button" aria-label={`Download ${m.file_name}`} onClick={() => void download(m)}>
                <Download size={15} />
              </button>
              <button className="icon-button" aria-label={`Delete ${m.file_name}`} onClick={() => setRemoving(m)}>
                <Trash2 size={15} />
              </button>
            </div>
          </li>
        ))}
      </ul>

      {removing && (
        <ConfirmDialog
          title="Delete material"
          message={`Delete “${removing.file_name}”? It will no longer be available for question generation.`}
          onClose={() => setRemoving(null)}
          onConfirm={async () => {
            await deleteMaterial(removing.id)
            materials.reload()
          }}
        />
      )}
    </section>
  )
}
