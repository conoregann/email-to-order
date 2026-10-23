import { useReducer, useState } from 'react'
import type { KeyboardEvent, ReactNode } from 'react'
import { CheckIcon, ChevronDownIcon, MinusIcon, PlusIcon } from '@radix-ui/react-icons'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { PageHeading } from '../components/page-heading'
import { ExtractionControls } from '../components/extraction-controls'
import { ErrorNotice } from '../components/error-notice'
import { Button } from '../components/ui/button'
import { Select } from '../components/ui/select'
import { QuantityResolution } from '../components/quantity-resolution'
import { AddCustomer } from '../components/add-customer'
import { AddProduct } from '../components/add-product'
import { editOrderLine } from '../lib/quantity-resolution'
import { sendJson } from '../lib/api'
import { availableStep, canContinueReview, initialProgress, reviewReducer, type ReviewStep } from '../lib/review-flow'
import { useResource } from '../lib/use-resource'
import { money, type Customer, type Line, type Order, type Product, type Values } from '../lib/types'

export function ReviewOrder() {
  const { orderId } = useParams()
  const resource = useResource<Order>(`/orders/${orderId}`)
  const customers = useResource<Customer[]>('/customers')
  const products = useResource<Product[]>('/catalogue/products')
  for (const item of [resource, customers, products]) {
    if (item.state.status === 'error') return <ErrorNotice error={item.state.error} retry={item.reload} />
  }
  if (resource.state.status !== 'ready' || customers.state.status !== 'ready' || products.state.status !== 'ready') return <p role="status">Loading order…</p>
  if (resource.state.data.status === 'confirmed') return <Navigate to={`/orders/${orderId}/confirmed`} replace />
  return <><PageHeading title="Review order" action={<Link className="back-link" to="/orders">Back to orders</Link>} />
    <DraftEditor key={resource.state.data.id} order={resource.state.data} customers={customers.state.data} onCustomersChange={customers.setData} products={products.state.data} onProductsChange={products.setData} onSave={resource.setData} onReload={resource.reload} />
  </>
}

function DraftEditor({ order, customers, onCustomersChange, products, onProductsChange, onSave, onReload }: { order: Order; customers: Customer[]; onCustomersChange: (customers: Customer[]) => void; products: Product[]; onProductsChange: (products: Product[]) => void; onSave: (order: Order) => void; onReload: () => void }) {
  const [values, setValues] = useState<Values>(() => structuredClone(order.values))
  const [lineApprovals, setLineApprovals] = useState(() => order.values.lines.map(() => false))
  const [progress, dispatch] = useReducer(reviewReducer, initialProgress)
  const [busy, setBusy] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [saved, setSaved] = useState('Saved')
  const navigate = useNavigate()
  const dirty = JSON.stringify(values) !== JSON.stringify(order.values)
  const locked = busy || extracting
  const customer = customers.find(customer => customer.id === values.customer_id)
  const unlocked = availableStep(progress)
  const approvalValues = { ...values, lines: values.lines.map((line, index) => ({ ...line, match_confirmed: line.match_confirmed && lineApprovals[index] })) }

  function focusStep(step: ReviewStep) {
    requestAnimationFrame(() => {
      const heading = document.getElementById(`review-heading-${step}`)
      heading?.focus({ preventScroll: true })
      heading?.scrollIntoView({ block: 'start', behavior: 'instant' })
    })
  }
  function openStep(step: ReviewStep) {
    if (locked || step > unlocked) return
    dispatch({ type: 'open', step }); focusStep(step)
  }
  function updateLine(index: number, patch: Partial<Line>) {
    setValues({ ...values, lines: values.lines.map((line, i) => i === index ? editOrderLine(line, patch) : line) })
    setLineApprovals(approvals => approvals.map((approved, i) => i === index ? patch.match_confirmed === true : approved))
    dispatch({ type: 'invalidate', step: 2 })
  }
  async function save() {
    const focused = document.activeElement as HTMLElement | null
    setBusy(true); setError(null)
    try {
      const updated = await sendJson<Order>(`/orders/${order.id}`, 'PUT', { ...values, version: order.version })
      setValues(structuredClone(updated.values)); onSave(updated); setSaved('Draft saved')
    } catch (error) { setError(error) } finally {
      setBusy(false)
      requestAnimationFrame(() => { if (focused?.isConnected && !focused.matches(':disabled')) focused.focus({ preventScroll: true }) })
    }
  }
  async function continueStep() {
    const step = progress.active
    if (locked || step === 3 || !canContinueReview(step, approvalValues, customers, products)) return
    dispatch({ type: 'complete', step })
    if (step === 2 && dirty) await save()
    focusStep((step + 1) as ReviewStep)
  }
  async function confirm() {
    setBusy(true); setError(null)
    try { await sendJson<Order>(`/orders/${order.id}/confirm`, 'POST', { version: order.version }); navigate(`/orders/${order.id}/confirmed`) }
    catch (error) { setError(error) } finally { setBusy(false) }
  }
  function keyboard(event: KeyboardEvent<HTMLDivElement>) {
    if (!(event.metaKey || event.ctrlKey) || event.nativeEvent.isComposing || event.repeat || (event.target as HTMLElement).closest('[role="listbox"]')) return
    if (event.key.toLowerCase() === 's') {
      event.preventDefault()
      if (!locked && dirty) void save()
    } else if (event.key === 'Enter') {
      event.preventDefault(); void continueStep()
    }
  }
  function acceptExtraction(updated: Order) {
    setValues(structuredClone(updated.values)); setLineApprovals(updated.values.lines.map(() => false)); onSave(updated); dispatch({ type: 'reset' }); focusStep(0)
  }
  const next = (label = 'Continue') => <div className="step-actions"><Button type="button" disabled={locked || !canContinueReview(progress.active, approvalValues, customers, products)} onClick={continueStep} aria-keyshortcuts="Control+Enter Meta+Enter">{label}</Button><span className="shortcut-hint"><kbd>Ctrl / ⌘</kbd> + <kbd>Enter</kbd></span></div>

  return <div className="review-grid" onKeyDown={keyboard}>
    <section className="email-panel" aria-label="Original customer email"><div className="email-heading"><h2>Customer email</h2><span className="source-label">{order.source === 'saved_example' ? 'Saved example · No AI' : order.source === 'ai_suggestion' ? 'AI suggestion' : 'Manual draft'}</span></div>
      <pre className="email-body">{order.original_email}</pre>
      {order.source === 'ai_suggestion' && <p className="form-help">Check every suggestion against this email.</p>}
      <details className="draft-history"><summary>Draft history</summary><details><summary>Reviewed values</summary><pre>{JSON.stringify(values, null, 2)}</pre></details>{order.extraction && <details><summary>AI extraction & provenance</summary><pre>{JSON.stringify(order.extraction, null, 2)}</pre></details>}<details><summary>Initial values</summary><pre>{JSON.stringify(order.initial_values, null, 2)}</pre></details></details>
    </section>
    <div className="review-flow">
      <div className="review-progress"><span>Review checklist</span><span aria-live="polite">{progress.completed.filter(Boolean).length} / 3 checked</span></div>
      <ExtractionControls order={order} disabled={dirty || locked} onUpdate={acceptExtraction} onBusy={setExtracting} />
      <ReviewSection step={0} title="Customer" summary={customer?.name} open={progress.active === 0} complete={progress.completed[0]} disabled={locked} onOpen={openStep}>
        <fieldset disabled={locked}><label htmlFor="customer">Customer</label><Select id="customer" value={values.customer_id ?? ''} disabled={locked} placeholder="Select customer" clearLabel="Clear customer" options={customers.map(customer => ({ value: customer.id, label: customer.name }))} onChange={value => { setValues({ ...values, customer_id: value || null, delivery_confirmed: false }); dispatch({ type: 'invalidate', step: 0 }) }} />
          <AddCustomer name={order.extraction?.facts.customer_name} email={order.extraction?.facts.customer_email} disabled={locked} onBusy={setBusy} onCreated={customer => {
            onCustomersChange([...customers, customer]); setValues({ ...values, customer_id: customer.id, delivery_confirmed: false }); dispatch({ type: 'invalidate', step: 0 })
          }} />
          <label className="checkbox review-approval"><input type="checkbox" checked={progress.completed[0]} disabled={!customer} onChange={event => { if (event.target.checked) { dispatch({ type: 'complete', step: 0 }); focusStep(1) } else { setValues({ ...values, delivery_confirmed: false }); dispatch({ type: 'invalidate', step: 0 }) } }} /><span>Customer matches the email.</span></label>
          {progress.completed[0] ? next() : <span className="shortcut-hint"><kbd>Space</kbd> to check</span>}
        </fieldset>
      </ReviewSection>
      <ReviewSection step={1} title="Delivery" summary={values.delivery_address} open={progress.active === 1} complete={progress.completed[1]} disabled={locked || unlocked < 1} onOpen={openStep}>
        <fieldset disabled={locked}>
          <label htmlFor="delivery-address">Delivery address</label><textarea id="delivery-address" rows={3} maxLength={1500} value={values.delivery_address} onChange={event => { setValues({ ...values, delivery_address: event.target.value, delivery_confirmed: false }); dispatch({ type: 'invalidate', step: 1 }) }} />
          {customer && <details className="optional-fields"><summary>Saved addresses</summary><label htmlFor="saved-address">Replace delivery address</label><Select id="saved-address" value={customer.addresses.find(address => address.lines.join(', ') === values.delivery_address)?.id ?? ''} disabled={locked} placeholder="Choose a saved address" options={customer.addresses.map(address => ({ value: address.id, label: `${address.label}: ${address.lines.join(', ')}` }))} onChange={value => { const address = customer.addresses.find(address => address.id === value); if (address) { setValues({ ...values, delivery_address: address.lines.join(', '), delivery_confirmed: false }); dispatch({ type: 'invalidate', step: 1 }) } }} /></details>}
          <details className="optional-fields"><summary>Delivery notes & date</summary><label htmlFor="delivery-instructions">Delivery instructions (optional)</label><textarea id="delivery-instructions" rows={2} maxLength={1500} value={values.delivery_instructions ?? ''} onChange={event => { setValues({ ...values, delivery_instructions: event.target.value }); dispatch({ type: 'invalidate', step: 1 }) }} /><label htmlFor="delivery-date">Requested date (optional)</label><input id="delivery-date" type="date" value={values.requested_delivery_date ?? ''} onChange={event => { setValues({ ...values, requested_delivery_date: event.target.value || null }); dispatch({ type: 'invalidate', step: 1 }) }} /><p className="form-help">Requested dates are not guaranteed.</p></details>
          <label className="checkbox review-approval"><input type="checkbox" checked={values.delivery_confirmed} disabled={!values.delivery_address.trim()} onChange={event => { setValues({ ...values, delivery_confirmed: event.target.checked }); if (event.target.checked) { dispatch({ type: 'complete', step: 1 }); focusStep(2) } else dispatch({ type: 'invalidate', step: 1 }) }} /><strong>I checked this address against the email and resolved any conflict.</strong></label>
          {values.delivery_confirmed ? next() : <span className="shortcut-hint"><kbd>Space</kbd> to check</span>}
        </fieldset>
      </ReviewSection>
      <ReviewSection step={2} title="Products" summary={`${values.lines.length} ${values.lines.length === 1 ? 'line' : 'lines'}`} open={progress.active === 2} complete={progress.completed[2]} disabled={locked || unlocked < 2} onOpen={openStep}>
        <fieldset disabled={locked}>{values.lines.map((line, index) => {
          const product = products.find(product => product.sku === line.sku)
          return <div className="line-card" key={index}><div className="line-heading"><h3>Product {index + 1}</h3><button type="button" className="text-button" onClick={() => { setValues({ ...values, lines: values.lines.filter((_, i) => i !== index) }); setLineApprovals(lineApprovals.filter((_, i) => i !== index)); dispatch({ type: 'invalidate', step: 2 }) }}>Remove</button></div>
            <label htmlFor={`requested-${index}`}>Requested in email</label><input id={`requested-${index}`} maxLength={300} value={line.requested_product} onChange={event => updateLine(index, { requested_product: event.target.value, match_confirmed: false })} />
            {line.requested_product === order.values.lines[index]?.requested_product && !line.sku && (order.validation.lines[index]?.candidates.length ?? 0) > 0 && <p className="notice">Possible matches: {order.validation.lines[index].candidates.join(', ')}</p>}
            <label htmlFor={`product-${index}`}>Catalogue product</label><Select id={`product-${index}`} value={line.sku ?? ''} disabled={locked} placeholder="Select exact product" clearLabel="Clear product" options={products.map(product => ({ value: product.sku, label: `${product.name} · ${product.pack_size} per case · ${product.sku}` }))} onChange={value => updateLine(index, { sku: value || null, match_confirmed: false })} />
            <AddProduct index={index} name={line.requested_product} disabled={locked} onBusy={setBusy} onCreated={product => { onProductsChange([...products, product]); updateLine(index, { sku: product.sku, match_confirmed: false }) }} />
            {product && <p className="product-facts">{money(product.price)} / case · {product.pack_size} units / case · {product.stock_cases} cases in simulated stock</p>}
            <div className="quantity-grid"><div><label htmlFor={`quantity-${index}`}>Quantity</label><div className="quantity-control"><button type="button" aria-label={`Decrease quantity for product ${index + 1}`} disabled={Number(line.quantity) <= 1} onClick={() => updateLine(index, { quantity: String(Math.max(1, Number(line.quantity || 0) - 1)), match_confirmed: false })}><MinusIcon /></button><input id={`quantity-${index}`} type="number" min="1" step="1" value={line.quantity ?? ''} onChange={event => updateLine(index, { quantity: event.target.value || null, match_confirmed: false })} /><button type="button" aria-label={`Increase quantity for product ${index + 1}`} onClick={() => updateLine(index, { quantity: String(Number(line.quantity || 0) + 1), match_confirmed: false })}><PlusIcon /></button></div></div><div><label htmlFor={`unit-${index}`}>Unit</label><Select id={`unit-${index}`} value={line.quantity_unit} disabled={locked} placeholder="Choose unit" options={[{ value: 'unknown', label: 'Choose unit' }, { value: 'case', label: 'Cases' }, { value: 'unit', label: 'Individual units' }]} onChange={value => updateLine(index, { quantity_unit: value as Line['quantity_unit'], match_confirmed: false })} /></div></div>
            <QuantityResolution orderId={order.id} index={index} line={line} disabled={locked} onChange={patch => updateLine(index, patch)} />
            <label className="checkbox review-approval"><input type="checkbox" checked={!!lineApprovals[index] && line.match_confirmed} disabled={!product || !(Number(line.quantity) > 0) || line.quantity_unit === 'unknown' || (!!line.quantity_resolution && line.quantity_resolution.status !== 'adjusted')} onChange={event => updateLine(index, { match_confirmed: event.target.checked })} /><span>{line.quantity_resolution?.status === 'adjusted' ? 'Product and approved quantity are correct.' : 'Product and quantity match the email.'}</span></label>
          </div>
        })}<Button variant="secondary" type="button" disabled={values.lines.length >= 50} onClick={() => { setValues({ ...values, lines: [...values.lines, { requested_product: '', sku: null, match_confirmed: false, quantity: null, quantity_unit: 'unknown' }] }); setLineApprovals([...lineApprovals, false]); dispatch({ type: 'invalidate', step: 2 }) }}>Add order line</Button>
          {next(dirty ? 'Save & check' : 'Review checks')}
        </fieldset>
      </ReviewSection>
      <ReviewSection step={3} title="Confirm" open={progress.active === 3} complete={false} disabled={locked || unlocked < 3} onOpen={openStep}>
        <div className="final-checks" aria-live="polite">{busy ? <p role="status">Checking draft…</p> : dirty ? <p className="notice">Save changes to refresh checks.</p> : <>
          {order.validation.issues.length > 0 ? <ul className="issue-list">{order.validation.issues.map((issue, index) => <li key={index} className={issue.severity}><span>{issue.field.startsWith('lines.') ? `Product ${Number(issue.field.split('.')[1]) + 1}: ` : ''}{issue.message}</span><button type="button" className="text-button" onClick={() => openStep(issue.field === 'customer_id' ? 0 : issue.field.startsWith('lines') ? 2 : 1)}>Review</button></li>)}</ul> : <p className="notice success">All checks passed.</p>}
          <dl className="confirmation-summary"><div><dt>Customer</dt><dd>{customer?.name}</dd></div><div><dt>Deliver to</dt><dd>{values.delivery_address}</dd></div>{values.delivery_instructions && <div><dt>Delivery notes</dt><dd>{values.delivery_instructions}</dd></div>}{values.requested_delivery_date && <div><dt>Requested date</dt><dd>{values.requested_delivery_date}</dd></div>}</dl>
          <div className="checked-lines">{order.validation.lines.map((line, index) => <div key={index}><span>{line.name ?? values.lines[index]?.requested_product}{line.cases != null && <small>{line.cases} cases</small>}</span><strong>{line.line_total ? money(line.line_total) : 'Unresolved'}</strong></div>)}</div>
          <p className="final-total"><span>Total</span><strong>{money(order.validation.total)}</strong></p>
        </>}</div>
        <div className="step-actions">{dirty && <Button variant="secondary" disabled={locked} onClick={save}>Save & check</Button>}<Button disabled={locked || dirty || !order.validation.can_confirm} onClick={confirm}>Confirm order</Button></div><p className="form-help">Demo confirmation. No email sent or stock reserved.</p>
      </ReviewSection>
      {error != null && <ErrorNotice error={error} />}
      <div className="draft-utility"><span role="status">{locked ? 'Working…' : dirty ? 'Unsaved changes' : saved}</span><Button variant="secondary" disabled={locked || !dirty} onClick={save} aria-keyshortcuts="Control+s Meta+s">Save draft</Button><button type="button" disabled={locked} className="text-button" onClick={() => { if (!dirty || window.confirm('Discard unsaved changes and reload this draft?')) onReload() }}>Reload</button></div>
    </div>
  </div>
}

function ReviewSection({ step, title, summary, open, complete, disabled, onOpen, children }: { step: ReviewStep; title: string; summary?: string; open: boolean; complete: boolean; disabled: boolean; onOpen: (step: ReviewStep) => void; children: ReactNode }) {
  return <section className="review-step" data-active={open} data-complete={complete}>
    <h2><button type="button" id={`review-heading-${step}`} className="step-heading" aria-label={`Step ${step + 1}: ${title}${complete ? ', checked' : ''}`} aria-expanded={open} aria-controls={`review-content-${step}`} disabled={disabled} onClick={() => onOpen(step)}><span className="step-number" aria-hidden="true">{complete ? <CheckIcon /> : step + 1}</span><span className="step-title">{title}{!open && complete && summary && <small>{summary}</small>}</span><ChevronDownIcon className="step-chevron" aria-hidden="true" /></button></h2>
    <div id={`review-content-${step}`} className="step-body" role="region" aria-labelledby={`review-heading-${step}`} hidden={!open}>{open && children}</div>
  </section>
}
