export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

const TOKEN_KEY = 'sib.token'

export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, message: string, code = 'error') {
    super(message)
    this.status = status
    this.code = code
  }
}

export const tokenStore = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token: string) {
    localStorage.setItem(TOKEN_KEY, token)
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY)
  },
}

type UnauthorizedHandler = () => void
let onUnauthorized: UnauthorizedHandler = () => {}

export function setUnauthorizedHandler(handler: UnauthorizedHandler) {
  onUnauthorized = handler
}

interface RequestOptions {
  method?: string
  body?: unknown
  formData?: FormData
  skipAuthRedirect?: boolean
}

function errorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string }
    if (first?.msg) return first.msg
  }
  return fallback
}

export async function request<T>(
  path: string,
  { method = 'GET', body, formData, skipAuthRedirect = false }: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {}
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your connection.', 'network')
  }

  if (response.status === 401 && !skipAuthRedirect) {
    tokenStore.clear()
    onUnauthorized()
  }
  if (!response.ok) {
    let data: { detail?: unknown; code?: string } = {}
    try {
      data = await response.json()
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(
      response.status,
      errorMessage(data.detail, `Request failed (${response.status})`),
      data.code,
    )
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function downloadBlob(path: string): Promise<Blob> {
  const token = tokenStore.get()
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your connection.', 'network')
  }
  if (response.status === 401) {
    tokenStore.clear()
    onUnauthorized()
  }
  if (!response.ok) throw new ApiError(response.status, `Download failed (${response.status})`)
  return response.blob()
}

export interface HealthResponse {
  status: string
}

export function getApiHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health', { skipAuthRedirect: true })
}
