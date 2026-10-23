import { useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { PageHeading } from '../components/page-heading'
import { ExtractionControls } from '../components/extraction-controls'
import { ErrorNotice } from '../components/error-notice'
import { Button } from '../components/ui/button'
import { sendJson } from '../lib/api'
import { useResource } from '../lib/use-resource'
import { money, type Customer, type Line, type Order, type Product, type Values } from '../lib/types'

export function ReviewOrder() {
  const { orderId } = useParams()
  const resource = useResource<Order>(`/orders/${orderId}`)
  const customers = useResource<Customer[]>('/customers')
  const products = useResource<Product[]>('/catalogue/products')
  const [message, setMessage] = useState('')
  for (const item of [resource, customers, products]) {
    if (item.state.status === 'error') return <ErrorNotice error={item.state.error} retry={item.reload} />
  }
  if (resource.state.status !== 'ready' || customers.state.status !== 'ready' || products.state.status !== 'ready') return <p role="status">Loading order and catalogue…</p>
  if (resource.state.data.status === 'confirmed') return <Navigate to={`/orders/${orderId}/confirmed`} replace />
  return <><PageHeading eyebrow="REVIEW ORDER" title="Check the details" description="Compare the draft with the original email before confirming." action={<Link className="back-link" to="/orders">← Back to orders</Link>} />
    {message && <p role="status" className="notice success">{message}</p>}
    <DraftEditor key={`${resource.state.data.id}:${resource.state.data.version}`} order={resource.state.data} customers={customers.state.data} products={products.state.data} onSave={order => { resource.setData(order); setMessage('Draft saved. Checks are up to date.') }} onReload={resource.reload} />
  </>
}
function DraftEditor({ order, customers, products, onSave, onReload }: { order: Order; customers: Customer[]; products: Product[]; onSave: (order: Order) => void; onReload: () => void }) {
  const [values, setValues] = useState<Values>(() => structuredClone(order.values))
  const [busy, setBusy] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const navigate = useNavigate()
  const dirty = JSON.stringify(values) !== JSON.stringify(order.values)
  const customer = customers.find(customer => customer.id === values.customer_id)
  function updateLine(index: number, patch: Partial<Line>) { setValues({ ...values, lines: values.lines.map((line, i) => i === index ? { ...line, ...patch } : line) }) }
  async function save() {
    setBusy(true); setError(null)
    try { onSave(await sendJson<Order>(`/orders/${order.id}`, 'PUT', { ...values, version: order.version })) }
    catch (error) { setError(error) } finally { setBusy(false) }
  }
  async function confirm() {
    setBusy(true); setError(null)
    try { await sendJson<Order>(`/orders/${order.id}/confirm`, 'POST', { version: order.version }); navigate(`/orders/${order.id}/confirmed`) }
    catch (error) { setError(error) } finally { setBusy(false) }
  }
  return <div className="review-grid"><section className="email-panel"><p className="eyebrow">ORIGINAL EMAIL</p><pre className="email-body">{order.original_email}</pre><p>{order.source === 'saved_example' ? 'Saved example — stored values, no AI.' : order.source === 'ai_suggestion' ? 'AI suggestion — review every field before confirmation.' : 'Manual — enter and review the order details.'}</p><details><summary>Draft history and extraction details</summary><details><summary>Current reviewed values</summary><pre>{JSON.stringify(values, null, 2)}</pre></details>{order.extraction && <details><summary>Validated AI extraction and provenance</summary><pre>{JSON.stringify(order.extraction, null, 2)}</pre></details>}<details><summary>Initial draft values</summary><pre>{JSON.stringify(order.initial_values, null, 2)}</pre></details></details></section>
    <section><h2>Order draft</h2><ExtractionControls order={order} disabled={dirty || busy} onUpdate={onSave} onBusy={setExtracting} /><fieldset disabled={busy || extracting}>
      <label htmlFor="customer">Customer</label><select id="customer" value={values.customer_id ?? ''} onChange={event => setValues({ ...values, customer_id: event.target.value || null, delivery_confirmed: false })}><option value="">Select customer</option>{customers.map(customer => <option key={customer.id} value={customer.id}>{customer.name}</option>)}</select>
      {customer && <><label htmlFor="saved-address">Use a saved delivery address</label><select id="saved-address" value="" onChange={event => { const address = customer.addresses.find(address => address.id === event.target.value); if (address) setValues({ ...values, delivery_address: address.lines.join(', '), delivery_confirmed: false }) }}><option value="">Choose to replace the address below</option>{customer.addresses.map(address => <option key={address.id} value={address.id}>{address.label}: {address.lines.join(', ')}</option>)}</select></>}
      <label htmlFor="delivery-address">Delivery address</label><textarea id="delivery-address" rows={3} maxLength={1500} value={values.delivery_address} onChange={event => setValues({ ...values, delivery_address: event.target.value, delivery_confirmed: false })} />
      <label className="checkbox"><input type="checkbox" checked={values.delivery_confirmed} onChange={event => setValues({ ...values, delivery_confirmed: event.target.checked })} />I checked this address against the email and resolved any conflict.</label>
      <label htmlFor="delivery-instructions">Delivery instructions</label><textarea id="delivery-instructions" rows={3} maxLength={1500} value={values.delivery_instructions ?? ''} onChange={event => setValues({ ...values, delivery_instructions: event.target.value })} />
      <label htmlFor="delivery-date">Requested delivery date (optional)</label><input id="delivery-date" type="date" value={values.requested_delivery_date ?? ''} onChange={event => setValues({ ...values, requested_delivery_date: event.target.value || null })} /><p>Requested dates are not guaranteed.</p>
      <h2>Products</h2>{values.lines.map((line, index) => {
        const product = products.find(product => product.sku === line.sku)
        return <div className="line-card" key={index}><h3>Line {index + 1}</h3>
          <label htmlFor={`requested-${index}`}>Requested product text</label><input id={`requested-${index}`} maxLength={300} value={line.requested_product} onChange={event => updateLine(index, { requested_product: event.target.value, match_confirmed: false })} />
          {!dirty && !line.sku && (order.validation.lines[index]?.candidates.length ?? 0) > 0 && <p className="notice">Possible matches: {order.validation.lines[index].candidates.join(', ')}. Select the product requested by the customer.</p>}
          <label htmlFor={`product-${index}`}>Catalogue product</label><select id={`product-${index}`} value={line.sku ?? ''} onChange={event => updateLine(index, { sku: event.target.value || null, match_confirmed: !!event.target.value })}><option value="">Select an exact product</option>{products.map(product => <option key={product.sku} value={product.sku}>{product.sku} — {product.name} ({product.pack_size} per case)</option>)}</select>
          {product && <><p>{money(product.price)} per case · {product.pack_size} units per case · {product.stock_cases} cases in simulated stock</p><label className="checkbox"><input type="checkbox" checked={line.match_confirmed} onChange={event => updateLine(index, { match_confirmed: event.target.checked })} />Product match reviewed</label></>}
          <div className="quantity-grid"><div><label htmlFor={`quantity-${index}`}>Quantity</label><input id={`quantity-${index}`} type="number" step="0.001" value={line.quantity ?? ''} onChange={event => updateLine(index, { quantity: event.target.value || null })} /></div><div><label htmlFor={`unit-${index}`}>Quantity unit</label><select id={`unit-${index}`} value={line.quantity_unit} onChange={event => updateLine(index, { quantity_unit: event.target.value as Line['quantity_unit'] })}><option value="unknown">Choose unit</option><option value="case">Cases</option><option value="unit">Individual units</option></select></div></div>
          {!dirty && order.validation.lines[index]?.line_total && <p>Line total: {money(order.validation.lines[index].line_total!)}</p>}
          <button type="button" className="text-button" onClick={() => setValues({ ...values, lines: values.lines.filter((_, i) => i !== index) })}>Remove line {index + 1}</button>
        </div>
      })}
      <Button variant="secondary" type="button" disabled={values.lines.length >= 50} onClick={() => setValues({ ...values, lines: [...values.lines, { requested_product: '', sku: null, match_confirmed: false, quantity: null, quantity_unit: 'unknown' }] })}>Add product line</Button>
    </fieldset>
    <div className="checks" aria-live="polite"><h2>Order checks</h2>{dirty ? <p className="notice">Unsaved changes. Save the draft to refresh checks and totals.</p> : <>
      {order.validation.issues.length ? <ul>{order.validation.issues.map((issue, index) => <li key={index} className={issue.severity}><strong>{issue.severity === 'blocker' ? 'Blocking issue' : 'Warning'}</strong>: {issue.field.startsWith('lines.') ? `Line ${Number(issue.field.split('.')[1]) + 1}: ` : ''}{issue.message}</li>)}</ul> : <p className="notice success">All checks passed. Ready to confirm.</p>}
      <p className="total">{order.validation.can_confirm ? 'Total' : 'Current calculated total'}: {money(order.validation.total)}</p></>}
    </div>
    {error != null && <ErrorNotice error={error} />}<div className="actions"><Button variant="secondary" disabled={busy || extracting || !dirty} onClick={save}>{busy ? 'Working…' : 'Save draft & check'}</Button><Button disabled={busy || extracting || dirty || !order.validation.can_confirm} onClick={confirm}>Confirm order</Button><button type="button" disabled={busy || extracting} className="text-button" onClick={() => { if (!dirty || window.confirm('Discard unsaved changes and reload this draft?')) onReload() }}>Reload saved draft</button></div>
    <p>Confirmation rechecks the order. Stock is simulated and is not reserved. No email will be sent.</p>
    </section></div>
}
