import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageHeading } from '../components/page-heading'
import { getJson, sendJson } from '../lib/api'
import { useResource } from '../lib/use-resource'
import type { Order } from '../lib/types'
import { Button } from '../components/ui/button'
import { ErrorNotice } from '../components/error-notice'

type Sample = { id: string; title: string; scenario: string; body: string }
export function NewOrder() {
  const { state, reload } = useResource<Sample[]>('/orders/samples')
  const config = useResource<{ enabled: boolean }>('/orders/extraction-config')
  const [email, setEmail] = useState('')
  const [selected, setSelected] = useState('')
  const [created, setCreated] = useState<Order | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const navigate = useNavigate()
  async function create(mode: 'manual' | 'saved' | 'ai') {
    setBusy(true); setError(null)
    let order = created
    try {
      order ??= await sendJson<Order>('/orders', 'POST', { email, sample_id: mode === 'saved' ? selected : null })
      setCreated(order)
      if (mode === 'ai') {
        await sendJson<Order>(`/orders/${order.id}/extract`, 'POST', { version: order.version, attempt_id: crypto.randomUUID() })
      }
      navigate(`/orders/${order.id}/review`)
    } catch (error) {
      setError(error)
      if (order) {
        // Recover durable status after a lost provider response; never create a replacement draft.
        try { setCreated(await getJson<Order>(`/orders/${order.id}`)) } catch { /* The review link remains usable. */ }
      }
    } finally { setBusy(false) }
  }
  return <><PageHeading eyebrow="NEW ORDER" title="Start with an email" description="Choose a fictional example or paste fictional customer email text." action={<Link className="back-link" to="/orders">← Back to orders</Link>} /><section>
    <label htmlFor="sample">Sample email</label>
    {state.status === 'loading' ? <p role="status">Loading sample emails…</p> : state.status === 'error' ? <ErrorNotice error={state.error} retry={reload} /> : <select id="sample" disabled={busy || !!created} value={selected} onChange={event => { setSelected(event.target.value); setEmail(state.data.find(sample => sample.id === event.target.value)?.body ?? '') }}><option value="">Choose a sample</option>{state.data.map(sample => <option key={sample.id} value={sample.id}>{sample.title}</option>)}</select>}
    <label htmlFor="email">Customer email</label><textarea id="email" rows={8} maxLength={20000} disabled={busy || !!created} value={email} onChange={event => { setEmail(event.target.value); setSelected('') }} placeholder="Paste fictional customer email text here" />
    <p className="form-help">Manual entry starts with blank fields. Saved examples use labelled stored values and do not contact AI.</p>
    {config.state.status === 'ready' && config.state.data.enabled ? <p className="form-help">Live extraction sends this email text to Google Gemini. Use fictional data only. AI suggestions require your review.</p> : <p className="form-help">Live extraction is unavailable. Manual entry and saved examples remain available.</p>}
    {created && <p role="status">Your email is saved. <Link to={`/orders/${created.id}/review`}>Open this draft to review, retry or continue manually</Link>.</p>}
    {busy && <p role="status">{created ? 'Extracting order suggestions…' : 'Saving email…'}</p>}
    {error != null && <ErrorNotice error={error} />}
    {!created && <div className="actions"><Button disabled={busy || !email.trim()} onClick={() => create('manual')}>Create manual draft</Button>
      {selected && <Button variant="secondary" disabled={busy} onClick={() => create('saved')}>Use saved example</Button>}
      {config.state.status === 'ready' && config.state.data.enabled && <Button disabled={busy || !email.trim()} onClick={() => create('ai')}>Extract with Gemini</Button>}
    </div>}
  </section></>
}
