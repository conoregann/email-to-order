import { useEffect, useState } from 'react'
import { Button } from './ui/button'
import { ErrorNotice } from './error-notice'
import { sendJson } from '../lib/api'
import { quantityRequest } from '../lib/quantity-resolution'
import type { Line, QuantitySuggestion } from '../lib/types'

export function QuantityResolution({ orderId, index, line, disabled, onChange }: { orderId: string; index: number; line: Line; disabled: boolean; onChange: (patch: Partial<Line>) => void }) {
  const { sku, quantity, quantity_unit: unit } = line
  const key = JSON.stringify([sku, quantity, unit])
  const [preview, setPreview] = useState<{ key: string; suggestion?: QuantitySuggestion | null; error?: unknown } | null>(null)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let active = true
    const timer = setTimeout(() => {
      sendJson<{ suggestion: QuantitySuggestion | null }>(`/orders/${orderId}/quantity-options`, 'POST', { sku, quantity, quantity_unit: unit })
        .then(result => { if (active) setPreview({ key, suggestion: result.suggestion }) })
        .catch(error => { if (active) setPreview({ key, error }) })
    }, 250)
    return () => { active = false; clearTimeout(timer) }
  }, [orderId, sku, quantity, unit, key, attempt])

  const suggestion = preview?.key === key ? preview.suggestion : null
  const resolution = line.quantity_resolution
  const request = quantityRequest(line)
  function approve(quantity: string, quantity_unit: Line['quantity_unit']) {
    onChange({ quantity, quantity_unit, match_confirmed: false, quantity_resolution: { ...request, status: 'adjusted', reason: request.reason.trim() || 'Whole-case quantity approved by staff.', approved_quantity: quantity, approved_unit: quantity_unit, approved_sku: line.sku } })
  }
  const requested = `${request.requested_quantity ?? 'Unspecified'} ${request.requested_unit === 'case' ? 'cases' : request.requested_unit === 'unit' ? 'units' : '(unit unclear)'}`
  return <>
    {preview?.key === key && preview.error != null && <ErrorNotice error={preview.error} retry={() => setAttempt(value => value + 1)} />}
    {(suggestion || resolution || unit === 'unknown') && <div className="quantity-resolution" aria-label={`Quantity decision for product ${index + 1}`}>
      <p><strong>{requested} requested{suggestion ? ` · ${suggestion.pack_size} per case` : ''}</strong></p>
      {suggestion && <p>{suggestion.cases} cases supplies {suggestion.supplied_units} units—{Number(suggestion.extra_units)} extra. Apply only after agreeing the quantity change.</p>}
      {unit === 'unknown' && <p>Choose cases or individual units before checking the pack size.</p>}
      {resolution?.status === 'needs_clarification' && <p role="status">Needs customer clarification. Save the draft to keep it pending; confirmation is blocked.</p>}
      {resolution?.status === 'unresolved' && <p role="status">Review the quantity change and record why it is acceptable before approving.</p>}
      {resolution?.status === 'adjusted' && <p role="status">Approved: {resolution.approved_quantity} {resolution.approved_unit === 'case' ? 'cases' : 'units'}. {resolution.reason}</p>}
      <label htmlFor={`quantity-reason-${index}`}>Reason / clarification note</label>
      <input id={`quantity-reason-${index}`} maxLength={500} value={resolution?.reason ?? ''} placeholder="Record customer agreement or what needs clarification" disabled={disabled} onChange={event => onChange({ quantity_resolution: { ...request, reason: event.target.value }, match_confirmed: false })} />
      <div className="quantity-decisions">
        {suggestion && <Button type="button" variant="secondary" disabled={disabled} onClick={() => approve(String(suggestion.cases), 'case')}>Use {suggestion.cases} cases ({suggestion.supplied_units} units)</Button>}
        {resolution && resolution.status !== 'adjusted' && !suggestion && preview?.key === key && preview.suggestion === null && unit !== 'unknown' && Number(quantity) > 0 && sku && <Button type="button" variant="secondary" disabled={disabled || !resolution.reason.trim()} onClick={() => approve(quantity!, unit)}>Approve quantity change</Button>}
        {resolution?.status !== 'needs_clarification' && <Button type="button" variant="secondary" disabled={disabled} onClick={() => onChange({ quantity_resolution: { ...request, status: 'needs_clarification', reason: request.reason.trim(), approved_quantity: null, approved_unit: 'unknown', approved_sku: null }, match_confirmed: false })}>Needs customer clarification</Button>}
      </div>
    </div>}
  </>
}
