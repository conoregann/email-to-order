import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { startWorkspace } from '../lib/api'
import { ErrorNotice } from './error-notice'

export function WorkspaceLayout() {
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let active = true
    startWorkspace().then(() => { if (active) setReady(true) }).catch(error => { if (active) setError(error) })
    return () => { active = false }
  }, [attempt])
  return <><a className="skip-link" href="#main-content">Skip to content</a><header className="app-header"><div className="header-inner"><Link to="/orders" className="brand"><span className="brand-mark" aria-hidden="true">↗</span>Email to Order <span className="demo-badge">DEMO</span></Link><nav aria-label="Main navigation"><NavLink to="/orders" end>Orders</NavLink><NavLink to="/orders/new">New order</NavLink></nav></div></header><main id="main-content">
    {error ? <ErrorNotice error={error} retry={() => { setError(null); setAttempt(value => value + 1) }} /> : ready ? <Outlet /> : <p role="status">Opening your guest workspace…</p>}
  </main><footer>Fictional distributor · Simulated stock · No emails are sent<br />Guest workspaces expire after 24 hours.</footer></>
}
