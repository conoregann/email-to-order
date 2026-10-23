import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageHeading } from '../components/page-heading'
import { getJson, sendJson } from '../lib/api'
import { useResource } from '../lib/use-resource'
import type { Order } from '../lib/types'
import { Select } from '../components/ui/select'
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
  const canExtract = config.state.status === 'ready' && config.state.data.enabled
  const primaryMode = selected ? 'saved' : canExtract ? 'ai' : 'manual'
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
  return <><PageHeading title="New order" action={<Link className="back-link" to="/orders">← Back to orders</Link>} /><section>
    <label htmlFor="sample">Sample email</label>
    {state.status === 'loading' ? <p role="status">Loading sample emails…</p> : state.status === 'error' ? <ErrorNotice error={state.error} retry={reload} /> : <Select id="sample" disabled={busy || !!created} value={selected} onChange={value => { setSelected(value); setEmail(state.data.find(sample => sample.id === value)?.body ?? '') }} placeholder="Choose a sample" clearLabel="Write my own email" options={state.data.map(sample => ({ value: sample.id, label: sample.title }))} />}
    <label htmlFor="email">Customer email</label><textarea id="email" rows={8} maxLength={20000} disabled={busy || !!created} value={email} onChange={event => { setEmail(event.target.value); setSelected('') }} placeholder="Paste fictional customer email text here" />
    {selected ? <p className="form-help">This sample opens with saved order details filled in. No AI is used. Review the product and delivery address before confirming.</p> : canExtract ? <p className="form-help">Create a draft from this email with Google Gemini, then review the suggestions. Use fictional data only.</p> : <p className="form-help">Choose a sample to start with filled-in details. For pasted emails, live extraction is unavailable; you can enter the details manually.</p>}
    {config.state.status === 'error' && <ErrorNotice error={config.state.error} retry={config.reload} />}
    {created && <p role="status">Your email is saved. <Link to={`/orders/${created.id}/review`}>Open this draft to review, retry or continue manually</Link>.</p>}
    {busy && <p role="status">{created ? 'Extracting order suggestions…' : 'Saving email…'}</p>}
    {error != null && <ErrorNotice error={error} />}
    {!created && <div className="actions"><Button disabled={busy || !email.trim() || config.state.status === 'loading'} onClick={() => create(primaryMode)}>{busy ? 'Preparing draft…' : primaryMode === 'manual' ? 'Create manual draft' : 'Create order draft'}</Button>
      {primaryMode !== 'manual' && <button type="button" className="text-button" disabled={busy || !email.trim()} onClick={() => create('manual')}>Enter details manually instead</button>}
    </div>}
  </section></>
}
