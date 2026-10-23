import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { sendJson } from '../lib/api'
import { useResource } from '../lib/use-resource'
import type { Order } from '../lib/types'
import { Button } from '../components/ui/button'
import { ErrorNotice } from '../components/error-notice'

type Sample = { id: string; title: string; scenario: string; body: string }
export function NewOrder() {
  const { state, reload } = useResource<Sample[]>('/orders/samples')
  const [email, setEmail] = useState('')
  const [selected, setSelected] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const navigate = useNavigate()
  async function create() {
    setBusy(true); setError(null)
    try {
      const order = await sendJson<Order>('/orders', 'POST', { email, sample_id: selected || null })
      navigate(`/orders/${order.id}/review`)
    } catch (error) { setError(error) } finally { setBusy(false) }
  }
  return <><p className="eyebrow">NEW ORDER</p><h1>Start with an email</h1><p>Choose a fictional example or paste customer email text.</p><section>
    <label htmlFor="sample">Sample email</label>
    {state.status === 'loading' ? <p role="status">Loading sample emails…</p> : state.status === 'error' ? <ErrorNotice error={state.error} retry={reload} /> : <select id="sample" disabled={busy} value={selected} onChange={event => { setSelected(event.target.value); setEmail(state.data.find(sample => sample.id === event.target.value)?.body ?? '') }}><option value="">Choose a sample</option>{state.data.map(sample => <option key={sample.id} value={sample.id}>{sample.title}</option>)}</select>}
    <label htmlFor="email">Customer email</label><textarea id="email" rows={12} maxLength={20000} disabled={busy} value={email} onChange={event => { setEmail(event.target.value); setSelected('') }} placeholder="Paste customer email text here" />
    <p>{selected ? 'Saved example values will prefill the draft. This is not live AI extraction.' : 'Manual draft: fill in the order details during review. AI extraction is coming in a later phase.'}</p>
    {error != null && <ErrorNotice error={error} />}
    <Button disabled={busy || !email.trim()} onClick={create}>{busy ? 'Creating draft…' : 'Create draft'}</Button>
  </section></>
}
