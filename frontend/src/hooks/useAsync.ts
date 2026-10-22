import { useCallback, useEffect, useState } from 'react'

interface AsyncState<T> {
  data: T | null
  error: string | null
  loading: boolean
  reload: () => void
}

/** Runs `fetcher` on mount and whenever its identity changes. Wrap it in useCallback. */
export function useAsync<T>(fetcher: () => Promise<T>): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    fetcher()
      .then((result) => {
        if (!active) return
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : 'Something went wrong.')
      })
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [fetcher, version])

  const reload = useCallback(() => setVersion((v) => v + 1), [])
  return { data, error, loading, reload }
}
