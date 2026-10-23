import { Link, useParams } from 'react-router-dom'
import { ErrorNotice } from '../components/error-notice'
import { Button } from '../components/ui/button'
import { useResource } from '../lib/use-resource'
import { money, type Order } from '../lib/types'

export function ConfirmedOrder() {
  const { orderId } = useParams()
  const { state, reload } = useResource<Order>(`/orders/${orderId}`)
  if (state.status === 'loading') return <p role="status">Loading confirmed order…</p>
  if (state.status === 'error') return <ErrorNotice error={state.error} retry={reload} />
  const order = state.data.confirmed
  if (!order) return <section><h1>This order is still a draft</h1><Link to={`/orders/${orderId}/review`}>Continue reviewing</Link></section>
  return <><p className="eyebrow">ORDER CONFIRMED</p><h1>{order.number}</h1><p>Confirmed orders are read-only. This demo does not send email or reserve stock.</p><section><h2>{order.customer.name}</h2><p className="preserve-text">{order.values.delivery_address}</p>
    <div className="table-scroll"><table><caption>Approved order lines</caption><thead><tr><th>Product</th><th>Cases</th><th>Units per case</th><th>Price per case</th><th>Total</th></tr></thead><tbody>{order.validation.lines.map((line, index) => <tr key={index}><td>{line.name}<br /><small>{line.sku}</small></td><td>{line.cases}</td><td>{line.pack_size}</td><td>{money(line.unit_price!)}</td><td>{money(line.line_total!)}</td></tr>)}</tbody></table></div><p className="total">Total: {money(order.validation.total)}</p>
    {order.values.requested_delivery_date && <p>Requested delivery: {order.values.requested_delivery_date} — not guaranteed.</p>}
    <h2>Simulated confirmation email</h2><pre className="preview">{order.confirmation_preview}</pre>
    {order.values.delivery_instructions && <p>Delivery instructions: {order.values.delivery_instructions}</p>}
    {state.data.extraction && <details><summary>Validated AI extraction and provenance</summary><pre>{JSON.stringify(state.data.extraction, null, 2)}</pre></details>}
    <details><summary>Approved values</summary><pre>{JSON.stringify(order.values, null, 2)}</pre></details>
    <details><summary>Original email and initial draft values</summary><pre>{state.data.original_email}</pre><pre>{JSON.stringify(state.data.initial_values, null, 2)}</pre></details>
  </section><Button asChild><Link to="/orders">Back to orders</Link></Button></>
}
