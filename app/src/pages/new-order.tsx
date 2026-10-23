import { useEffect, useState } from 'react'
import { getJson } from '../lib/api'
import { Button } from '../components/ui/button'

type Sample = { id: string; title: string; scenario: string; body: string }
export function NewOrder() {
  const [samples, setSamples] = useState<Sample[]>([])
  const [email, setEmail] = useState('')
  const [selected, setSelected] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    getJson<Sample[]>('/orders/samples', controller.signal)
      .then(setSamples)
      .catch((err: unknown) => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : 'Could not load samples.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [attempt])
  return <><p className="eyebrow">NEW ORDER</p><h1>Start with an email</h1><p>Choose a fictional example or paste customer email text.</p><section>
    <label htmlFor="sample">Sample email</label>
    {loading ? <p role="status">Loading sample emails…</p> : error ? <div role="alert"><p>{error}</p><Button onClick={() => { setLoading(true); setError(''); setAttempt(attempt + 1) }}>Retry samples</Button></div> : <select id="sample" value={selected} onChange={event => { setSelected(event.target.value); setEmail(samples.find(sample => sample.id === event.target.value)?.body ?? '') }}><option value="">Choose a sample</option>{samples.map(sample => <option key={sample.id} value={sample.id}>{sample.title}</option>)}</select>}
    {selected && <p>{samples.find(sample => sample.id === selected)?.scenario}</p>}
    <label htmlFor="email">Customer email</label><textarea id="email" rows={12} maxLength={20000} value={email} onChange={event => { setEmail(event.target.value); setSelected('') }} placeholder="Paste customer email text here" />
    <p>Samples are loaded from the backend. Draft creation and validation are the next development step.</p><Button disabled>Create draft — coming next</Button>
  </section></>
}
