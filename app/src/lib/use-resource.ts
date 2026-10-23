import { useEffect, useState } from 'react'
import { getJson } from './api'

type State<T> = ({ status: 'loading' } | { status: 'error'; error: unknown } | { status: 'ready'; data: T }) & { path: string }
export function useResource<T>(path: string) {
  const [state, setState] = useState<State<T>>({ status: 'loading', path })
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    getJson<T>(path, controller.signal)
      .then(data => { if (!controller.signal.aborted) setState({ status: 'ready', data, path }) })
      .catch(error => { if (!controller.signal.aborted) setState({ status: 'error', error, path }) })
    return () => controller.abort()
  }, [path, attempt])
  return { state: state.path === path ? state : { status: 'loading', path } as State<T>, reload: () => { setState({ status: 'loading', path }); setAttempt(value => value + 1) },
    setData: (data: T) => setState({ status: 'ready', data, path }) }
}
