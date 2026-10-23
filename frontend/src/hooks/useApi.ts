import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'

interface UseApiOptions {
  deps?: unknown[]
  skip?: boolean
}

export function useApi<T>(path: string, options: UseApiOptions = {}) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    if (options.skip) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.get<T>(path)
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }, [path, options.skip])

  useEffect(() => {
    fetch()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetch, ...(options.deps ?? [])])

  return { data, loading, error, refetch: fetch }
}
