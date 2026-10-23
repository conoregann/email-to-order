import { Link } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { ErrorNotice } from '../components/error-notice'
import { useResource } from '../lib/use-resource'
import { money, type Order } from '../lib/types'

export function Orders() {
  const { state, reload } = useResource<Order[]>('/orders')
  return <><div className="heading"><div><p className="eyebrow">WORKSPACE</p><h1>Orders</h1><p>Review customer emails, resolve issues and confirm orders.</p></div><Button asChild><Link to="/orders/new">New order</Link></Button></div>
    {state.status === 'loading' ? <p role="status">Loading orders…</p> : state.status === 'error' ? <ErrorNotice error={state.error} retry={reload} /> : state.data.length === 0 ? <section><h2>No orders yet</h2><p>Start with a sample email or paste an email to create your first draft.</p></section> : <section className="order-list" aria-label="Order history">{state.data.map(order => <article key={order.id}><div><span className={`badge ${order.status}`}>{order.status}</span><h2><Link to={`/orders/${order.id}/${order.status === 'confirmed' ? 'confirmed' : 'review'}`}>{order.confirmed?.number ?? `Draft ${order.id.slice(0, 8)}`}</Link></h2><p>{new Date(order.created_at * 1000).toLocaleString('en-IE')} · {order.values.lines.length} line(s)</p></div><div>{money(order.validation.total)}{order.status === 'draft' && <p>{order.validation.issues.filter(issue => issue.severity === 'blocker').length} blocking issue(s)</p>}</div></article>)}</section>}
  </>
}
