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
    {order.extraction_message && <p role="status">{order.extraction_message}</p>}
    {running ? <p role="status">Extraction is running. Reload its status after a lost response. An interrupted attempt expires automatically.</p> : <p>Live extraction sends the original text to Google Gemini. Use fictional data only. Every suggestion needs review.</p>}
    {busy && <p role="status">Working… Your email is saved.</p>}
    {error != null && <ErrorNotice error={error} />}
    <div className="actions">
      {!running && config.state.status === 'ready' && config.state.data.enabled && <Button disabled={busy || disabled} onClick={() => action('extract')}>{order.extraction_status === 'failed' ? 'Retry extraction' : 'Extract with Gemini'}</Button>}
      {!running && samples.state.status === 'ready' && samples.state.data.some(sample => sample.body === order.original_email) && <Button disabled={busy || disabled} onClick={() => action('saved-example')}>Use saved example (no AI)</Button>}
      <button type="button" className="text-button" disabled={busy || disabled} onClick={() => action('reload')}>Reload extraction status</button>
    </div>
    <p>{disabled ? 'Save or discard your edits before changing the draft source.' : 'You can also enter and save the order details manually below.'}</p>
  </div>
}
