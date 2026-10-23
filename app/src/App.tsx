import { useEffect, useState } from 'react'
import { BrowserRouter, Link, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { startWorkspace } from './lib/api'
import { ErrorNotice } from './components/error-notice'
import { NewOrder } from './pages/new-order'
import { Orders } from './pages/orders'
import { ReviewOrder } from './pages/review-order'
import { ConfirmedOrder } from './pages/confirmed-order'

function Layout() {
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let active = true
    startWorkspace().then(() => { if (active) setReady(true) }).catch(error => { if (active) setError(error) })
    return () => { active = false }
  }, [attempt])
  return <><header><Link to="/orders" className="brand">Email to Order <span>DEMO</span></Link><Link to="/orders">Orders</Link></header><main>
    {error ? <ErrorNotice error={error} retry={() => { setError(null); setAttempt(value => value + 1) }} /> : ready ? <Outlet /> : <p role="status">Opening your guest workspace…</p>}
  </main><footer>Fictional distributor · Simulated stock · No emails are sent<br />Guest workspaces expire after 24 hours.</footer></>
}
export default function App() {
  return <BrowserRouter><Routes><Route element={<Layout />}><Route index element={<Navigate to="/orders" replace />} /><Route path="orders" element={<Orders />} /><Route path="orders/new" element={<NewOrder />} /><Route path="orders/:orderId/review" element={<ReviewOrder />} /><Route path="orders/:orderId/confirmed" element={<ConfirmedOrder />} /><Route path="*" element={<section><h1>Page not found</h1><Link to="/orders">Back to orders</Link></section>} /></Route></Routes></BrowserRouter>
}
