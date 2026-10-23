import { Link } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { PageHeading } from '../components/page-heading'
import { ErrorNotice } from '../components/error-notice'
import { useResource } from '../lib/use-resource'
import { money, type Order } from '../lib/types'

export function Orders() {
  const { state, reload } = useResource<Order[]>('/orders')
  return <>
    <PageHeading eyebrow="WORKSPACE" title="Orders" description="Turn customer emails into checked, ready-to-confirm orders." action={<Button asChild><Link to="/orders/new"><span aria-hidden="true">＋</span> New order</Link></Button>} />
    {state.status === 'loading' ? <p role="status">Loading orders…</p> : state.status === 'error' ? <ErrorNotice error={state.error} retry={reload} /> : state.data.length === 0 ? <section className="empty-state">
      <span className="empty-icon" aria-hidden="true">↗</span><p className="eyebrow">EMAIL TO ORDER</p><h2>Your first order starts here</h2><p>Choose a sample email or paste a fictional customer request.<br />Review the details, check the products, then confirm.</p><Button asChild><Link to="/orders/new">Create your first draft <span aria-hidden="true">→</span></Link></Button>
    </section> : <section className="order-list" aria-label="Order history"><div className="list-heading"><h2>Order history</h2><span>{state.data.length} {state.data.length === 1 ? 'order' : 'orders'}</span></div>{state.data.map(order => <OrderRow key={order.id} order={order} />)}</section>}
  </>
}

function OrderRow({ order }: { order: Order }) {
  const confirmed = order.status === 'confirmed'
  const blockers = order.validation.issues.filter(issue => issue.severity === 'blocker').length
  const destination = `/orders/${order.id}/${confirmed ? 'confirmed' : 'review'}`
  return <article className="order-row">
    <div className="order-details"><span className={`badge ${order.status}`}>{confirmed ? 'Confirmed' : 'Draft'}</span><h3><Link to={destination}>{order.confirmed?.number ?? `Draft ${order.id.slice(0, 8)}`}</Link></h3><p>{new Date(order.created_at * 1000).toLocaleString('en-IE')} · {order.values.lines.length} {order.values.lines.length === 1 ? 'line' : 'lines'}</p></div>
    <div className="order-amount"><strong>{money(order.validation.total)}</strong>{!confirmed && <p className={blockers ? 'blocker' : ''}>{blockers ? `${blockers} blocking ${blockers === 1 ? 'issue' : 'issues'}` : order.validation.can_confirm ? 'Ready to confirm' : 'Review required'}</p>}</div>
    <Button asChild variant="secondary"><Link to={destination} aria-label={`${confirmed ? 'View' : 'Review'} ${order.confirmed?.number ?? `draft ${order.id.slice(0, 8)}`}`}>{confirmed ? 'View order' : 'Review draft'} <span aria-hidden="true">→</span></Link></Button>
  </article>
}
