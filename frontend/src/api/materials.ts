import { API_BASE_URL, ApiError, downloadBlob, request, tokenStore } from './client'

export type MaterialStatus = 'uploaded' | 'extracting' | 'ready' | 'failed'

export interface Material {
  id: string
  course_id: string
  topic_id: string
  uploaded_by: string
  file_name: string
  file_type: 'pdf' | 'pptx' | 'docx'
  file_size_bytes: number
  status: MaterialStatus
  error_message: string | null
  created_at: string
}

export const ALLOWED_EXTENSIONS = ['pdf', 'pptx', 'docx']
export const MAX_UPLOAD_MB = 25

/** Client-side pre-check; the server remains the source of truth. */
export function validateFile(file: File): string | null {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (!ALLOWED_EXTENSIONS.includes(ext)) return 'Only PDF, PPTX and DOCX files can be uploaded.'
  if (file.size === 0) return 'The file is empty.'
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `The file is larger than ${MAX_UPLOAD_MB} MB.`
  return null
}

export const listMaterials = (courseId: string, topicId?: string) =>
  request<Material[]>(`/courses/${courseId}/materials${topicId ? `?topic_id=${topicId}` : ''}`)

export const deleteMaterial = (id: string) =>
  request<void>(`/materials/${id}`, { method: 'DELETE' })

export async function saveMaterial(material: Material): Promise<void> {
  const blob = await downloadBlob(`/materials/${material.id}/download`)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = material.file_name
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

/** Uses XHR (not fetch) so upload progress can be reported. */
export function uploadMaterial(
  courseId: string,
  topicId: string,
  file: File,
  onProgress: (fraction: number) => void,
): Promise<Material> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE_URL}/courses/${courseId}/topics/${topicId}/materials`)
    const token = tokenStore.get()
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total)
    }
    xhr.onerror = () => reject(new ApiError(0, 'Cannot reach the server. Check your connection.', 'network'))
    xhr.onload = () => {
      let data: { detail?: unknown; code?: string } = {}
      try {
        data = JSON.parse(xhr.responseText)
      } catch {
        /* non-JSON body */
      }
      if (xhr.status >= 200 && xhr.status < 300) return resolve(data as unknown as Material)
      const detail = typeof data.detail === 'string' ? data.detail : `Upload failed (${xhr.status})`
      reject(new ApiError(xhr.status, detail, data.code))
    }
    const form = new FormData()
    form.append('file', file)
    xhr.send(form)
  })
}
