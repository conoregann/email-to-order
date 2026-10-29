import { useState } from 'react'
import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { PageHeading } from '../components/page-heading'
import { ErrorNotice } from '../components/error-notice'
import { useResource } from '../lib/use-resource'
import { money, type Customer, type Order } from '../lib/types'

export function Orders() {
  const [filter, setFilter] = useState<'all' | 'draft' | 'confirmed'>('all')
  const [page, setPage] = useState(0)
  const pageSize = 25
  const { state, reload } = useResource<{ items: Order[]; total: number }>(`/orders?limit=${pageSize}&offset=${page * pageSize}${filter === 'all' ? '' : `&status=${filter}`}`)
  const customers = useResource<Customer[]>('/customers')
  return <>
    <PageHeading title="Orders" action={<Button asChild><Link to="/orders/new"><span aria-hidden="true">＋</span> New order</Link></Button>} />
    {state.status === 'loading' ? <p role="status">Loading orders…</p> : state.status === 'error' ? <ErrorNotice error={state.error} retry={reload} /> : <>
      <p>Overview of orders on the current page.</p>
      <OrderOverview orders={state.data.items} />
      <section className="order-list" aria-label="Order history">
        <div className="list-heading"><h2>Order history</h2>
          <div className="order-filters" role="group" aria-label="Filter orders">
            {(['all', 'draft', 'confirmed'] as const).map(value => <button key={value} type="button" aria-pressed={filter === value} onClick={() => { setFilter(value); setPage(0) }}>{value === 'all' ? 'All' : value === 'draft' ? 'Drafts' : 'Confirmed'}</button>)}
          </div>
        </div>
        <div aria-live="polite">
          {state.data.items.map(order => <OrderRow key={order.id} order={order} customers={customers.state.status === 'ready' ? customers.state.data : []} />)}
          {state.data.items.length === 0 && <p className="filtered-empty">{filter === 'all' ? 'No orders yet.' : filter === 'draft' ? 'No drafts yet.' : 'No confirmed orders yet.'}</p>}
        </div>
        <nav className="order-pagination" aria-label="Order history pages">
          <span className="pagination-summary">{state.data.total === 0 ? '0 orders' : `${page * pageSize + 1}–${page * pageSize + state.data.items.length} of ${state.data.total} ${state.data.total === 1 ? 'order' : 'orders'}`}</span>
          <div className="pagination-controls">
            <Button variant="secondary" disabled={page === 0} onClick={() => setPage(page - 1)}><span aria-hidden="true">←</span> Previous</Button>
            <span className="pagination-page">Page {page + 1} of {Math.max(1, Math.ceil(state.data.total / pageSize))}</span>
            <Button variant="secondary" disabled={(page + 1) * pageSize >= state.data.total} onClick={() => setPage(page + 1)}>Next <span aria-hidden="true">→</span></Button>
          </div>
        </nav>
      </section>
    </>}
  </>
}

function OrderRow({ order, customers }: { order: Order; customers: Customer[] }) {
  const confirmed = order.status === 'confirmed'
  const blockers = order.validation.issues.filter(issue => issue.severity === 'blocker').length
  const customer = order.confirmed?.customer.name ?? customers.find(customer => customer.id === order.values.customer_id)?.name ?? (order.values.customer_id ? 'Customer' : 'Customer not selected')
  const clarifications = order.values.lines.filter(line => line.quantity_resolution?.status === 'needs_clarification').length
  const firstLine = order.values.lines[0]
  const destination = `/orders/${order.id}/${confirmed ? 'confirmed' : 'review'}`
  return <article className="order-row">
    <div className="order-details"><div className="order-identity"><h3><Link to={destination}>{customer}</Link></h3></div><p>{order.confirmed?.number ?? order.id.slice(0, 8)} · {new Date(order.created_at * 1000).toLocaleDateString('en-IE', { day: 'numeric', month: 'short' })}</p></div>
    <div className="order-products"><strong>{order.validation.lines[0]?.name || firstLine?.requested_product || 'No product selected'}</strong><span>{firstLine ? `${firstLine.quantity ?? '—'} ${firstLine.quantity_unit === 'case' ? 'cases' : firstLine.quantity_unit === 'unit' ? 'units' : '· unit needed'}` : 'Add a product'}{order.values.lines.length > 1 && ` · +${order.values.lines.length - 1} more`}</span></div>
    <span className={`order-status badge ${order.status}`}>{confirmed ? 'Confirmed' : 'Draft'}</span>
    <div className="order-amount"><strong>{money(order.validation.total)}</strong>{!confirmed && <p className={blockers ? 'blocker' : ''}>{clarifications ? 'Needs clarification' : blockers ? `${blockers} to resolve` : order.validation.can_confirm ? 'Ready to confirm' : 'Review needed'}</p>}</div>
    <Button asChild variant="secondary"><Link to={destination} aria-label={`${confirmed ? 'View' : 'Review'} ${order.confirmed?.number ?? `draft ${order.id.slice(0, 8)}`}`}>{confirmed ? 'View order' : 'Review draft'} <span aria-hidden="true">→</span></Link></Button>
  </article>
}

function OrderOverview({ orders }: { orders: Order[] }) {
  const drafts = orders.filter(order => order.status === 'draft')
  const confirmed = orders.filter(order => order.status === 'confirmed')
  const blockers = drafts.reduce((count, order) => count + order.validation.issues.filter(issue => issue.severity === 'blocker').length, 0)
  const ready = drafts.filter(order => order.validation.can_confirm).length
  const confirmedCents = confirmed.reduce((total, order) => total + Math.round(Number(order.confirmed?.validation.total ?? order.validation.total) * 100), 0)
  return <div className="overview-grid" aria-label="Current page overview">
    <section className="overview-card overview-mix"><h2>Orders on this page</h2><div className="metric-value">{orders.length}<span>total {orders.length === 1 ? 'order' : 'orders'}</span></div>
      <div className="mix-chart" role="img" aria-label={`${drafts.length} drafts and ${confirmed.length} confirmed orders`}>{orders.length > 0 && <>{drafts.length > 0 && <span className="mix-drafts" style={{ '--share': `${drafts.length / orders.length * 100}%` } as CSSProperties} />}{confirmed.length > 0 && <span className="mix-confirmed" style={{ '--share': `${confirmed.length / orders.length * 100}%` } as CSSProperties} />}</>}</div>
      <dl className="mix-legend"><div><dt>Drafts</dt><dd>{drafts.length}</dd></div><div><dt>Confirmed</dt><dd>{confirmed.length}</dd></div></dl>
    </section>
    <section className="overview-card overview-review"><h2>Awaiting review</h2><div className="metric-value">{drafts.length}</div><p>{`${blockers} blocking ${blockers === 1 ? 'issue' : 'issues'}`}</p><span className="metric-note">{ready} ready to confirm</span></section>
    <section className="overview-card overview-value"><h2>Confirmed value</h2><div className="metric-value">{money((confirmedCents / 100).toFixed(2))}</div><p>{`${confirmed.length} confirmed ${confirmed.length === 1 ? 'order' : 'orders'}`}</p><span className="metric-note">EUR</span></section>
  </div>
}
