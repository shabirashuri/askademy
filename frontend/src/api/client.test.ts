import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, request, setUnauthorizedHandler, tokenStore } from './client'

function jsonResponse(status: number, body: unknown) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('request', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    setUnauthorizedHandler(() => {})
  })

  it('sends the stored bearer token and parses JSON', async () => {
    tokenStore.set('tok-123')
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, { ok: true }))

    const result = await request<{ ok: boolean }>('/auth/me')

    expect(result).toEqual({ ok: true })
    const [url, init] = vi.mocked(fetch).mock.calls[0]
    expect(String(url)).toMatch(/\/auth\/me$/)
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer tok-123')
  })

  it('turns API error bodies into ApiError with the server detail', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse(409, { detail: 'A course with this code already exists.', code: 'conflict' }),
    )

    const error = (await request('/courses', { method: 'POST', body: {} }).catch((e) => e)) as ApiError

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(409)
    expect(error.code).toBe('conflict')
    expect(error.message).toBe('A course with this code already exists.')
  })

  it('clears the token and notifies on 401', async () => {
    tokenStore.set('expired')
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    vi.mocked(fetch).mockResolvedValue(jsonResponse(401, { detail: 'Invalid or expired token.' }))

    await expect(request('/auth/me')).rejects.toBeInstanceOf(ApiError)

    expect(tokenStore.get()).toBeNull()
    expect(onUnauthorized).toHaveBeenCalledOnce()
  })

  it('does not treat a failed login as a session expiry', async () => {
    tokenStore.set('keep-me')
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    vi.mocked(fetch).mockResolvedValue(jsonResponse(401, { detail: 'Invalid email or password.' }))

    await expect(request('/auth/login', { skipAuthRedirect: true })).rejects.toThrow(
      'Invalid email or password.',
    )

    expect(onUnauthorized).not.toHaveBeenCalled()
  })

  it('reports a network failure as a readable ApiError', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'))

    const error = (await request('/courses').catch((e) => e)) as ApiError

    expect(error).toBeInstanceOf(ApiError)
    expect(error.code).toBe('network')
    expect(error.message).toMatch(/cannot reach the server/i)
  })
})

describe('tokenStore', () => {
  it('survives storage being unavailable', () => {
    const spy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    expect(tokenStore.get()).toBeNull()
    spy.mockRestore()
  })
})
