import { BrowserRouter, Link, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { Button } from './components/ui/button'
import { NewOrder } from './pages/new-order'

function Layout() {
  return <><header><Link to="/orders" className="brand">Email to Order <span>DEMO</span></Link><Link to="/orders">Orders</Link></header><main><Outlet /></main><footer>Fictional distributor · Simulated stock · No emails are sent</footer></>
}
function Orders() {
  return <><div className="heading"><div><p className="eyebrow">WORKSPACE</p><h1>Orders</h1><p>Turn customer emails into checked, editable orders.</p></div><Button asChild><Link to="/orders/new">New order</Link></Button></div><section><h2>Your orders will appear here</h2><p>Start with a sample email or paste an email. Draft editing and confirmation are coming in the next iteration.</p></section></>
}
function PendingOrder({ confirmed = false }: { confirmed?: boolean }) {
  return <section><h1>{confirmed ? 'Confirmed order' : 'Review order'}</h1><p>This route is ready for the manual order workflow. No order has been loaded or confirmed.</p><Button asChild><Link to="/orders">Back to orders</Link></Button></section>
}
export default function App() {
  return <BrowserRouter><Routes><Route element={<Layout />}><Route index element={<Navigate to="/orders" replace />} /><Route path="orders" element={<Orders />} /><Route path="orders/new" element={<NewOrder />} /><Route path="orders/:orderId/review" element={<PendingOrder />} /><Route path="orders/:orderId/confirmed" element={<PendingOrder confirmed />} /><Route path="*" element={<section><h1>Page not found</h1><Link to="/orders">Back to orders</Link></section>} /></Route></Routes></BrowserRouter>
}
