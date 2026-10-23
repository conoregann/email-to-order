import { useState } from 'react'
import { getJson, sendJson } from '../lib/api'
import { useResource } from '../lib/use-resource'
import type { Order } from '../lib/types'
import { Button } from './ui/button'
import { ErrorNotice } from './error-notice'

export function ExtractionControls({ order, disabled, onUpdate, onBusy }: { order: Order; disabled: boolean; onUpdate: (order: Order) => void; onBusy: (busy: boolean) => void }) {
  const config = useResource<{ enabled: boolean }>('/orders/extraction-config')
  const samples = useResource<{ body: string }[]>('/orders/samples')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const eligible = order.source === 'manual' && order.version === 1 && order.status === 'draft'
  const running = order.extraction_status === 'running'
  async function action(kind: 'extract' | 'saved-example' | 'reload') {
    setBusy(true); onBusy(true); setError(null)
    try {
      const updated = kind === 'reload' ? await getJson<Order>(`/orders/${order.id}`) : await sendJson<Order>(`/orders/${order.id}/${kind}`, 'POST', {
        version: order.version, ...(kind === 'extract' ? { attempt_id: crypto.randomUUID() } : {}),
      })
      onUpdate(updated)
    } catch (error) {
      setError(error)
      try { onUpdate(await getJson<Order>(`/orders/${order.id}`)) } catch { /* Preserve the current draft and recovery controls. */ }
    } finally { setBusy(false); onBusy(false) }
  }
  if (!eligible) return null
  return <div className="notice">
    <h3>Fill in this draft</h3>
    {order.extraction_message && <p role="status">{order.extraction_message}</p>}
    {running ? <p role="status">Extracting details from your email…</p> : <p>{samples.state.status === 'ready' && samples.state.data.some(sample => sample.body === order.original_email) ? 'This sample has saved details ready to use. Fill them in, then review the product and address.' : config.state.status === 'ready' && config.state.data.enabled ? 'Extract suggestions with Google Gemini, then review each field. Use fictional data only.' : 'Live extraction is unavailable. Enter the order details below.'}</p>}
    {config.state.status === 'error' && <ErrorNotice error={config.state.error} retry={config.reload} />}
    {busy && <p role="status">Working… Your email is saved.</p>}
    {error != null && <ErrorNotice error={error} />}
    <div className="actions">
      {!running && config.state.status === 'ready' && config.state.data.enabled && <Button disabled={busy || disabled} onClick={() => action('extract')}>{order.extraction_status === 'failed' ? 'Retry extraction' : 'Extract with Gemini'}</Button>}
      {!running && samples.state.status === 'ready' && samples.state.data.some(sample => sample.body === order.original_email) && <Button disabled={busy || disabled} onClick={() => action('saved-example')}>Fill from sample (no AI)</Button>}
      {(running || error != null) && <button type="button" className="text-button" disabled={busy || disabled} onClick={() => action('reload')}>Check extraction status</button>}
    </div>
    <p>{disabled ? 'Save or discard your edits before changing the draft source.' : 'You can also enter and save the order details manually below.'}</p>
  </div>
}
