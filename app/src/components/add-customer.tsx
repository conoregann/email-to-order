import { useState } from 'react'
import type { FormEvent } from 'react'
import { sendJson } from '../lib/api'
import type { Customer } from '../lib/types'
import { ErrorNotice } from './error-notice'
import { Button } from './ui/button'

export function AddCustomer({ name = '', email = '', disabled, onCreated, onBusy }: { name?: string; email?: string; disabled: boolean; onCreated: (customer: Customer) => void; onBusy: (busy: boolean) => void }) {
  const [open, setOpen] = useState(false)
  const [customerName, setCustomerName] = useState(name)
  const [customerEmail, setCustomerEmail] = useState(email)
  const [error, setError] = useState<unknown>(null)
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (disabled) return
    onBusy(true); setError(null)
    try {
      const customer = await sendJson<Customer>('/customers', 'POST', { name: customerName, email: customerEmail })
      onCreated(customer); setOpen(false)
    } catch (error) { setError(error) } finally { onBusy(false) }
  }
  if (!open) return <button type="button" className="text-button" disabled={disabled} onClick={() => { setCustomerName(name); setCustomerEmail(email); setOpen(true) }}>Add new customer</button>
  return <form onSubmit={create} aria-label="Add new customer">
    <p className="form-help">Save this customer in this workspace. Review their delivery address in the next step.</p>
    <label htmlFor="new-customer-name">Customer name</label><input id="new-customer-name" required maxLength={200} value={customerName} disabled={disabled} onChange={event => setCustomerName(event.target.value)} autoFocus />
    <label htmlFor="new-customer-email">Customer email</label><input id="new-customer-email" type="email" required maxLength={320} value={customerEmail} disabled={disabled} onChange={event => setCustomerEmail(event.target.value)} />
    {error != null && <ErrorNotice error={error} />}
    <div className="actions"><Button type="submit" disabled={disabled || !customerName.trim() || !customerEmail.trim()}>Save and select customer</Button><button type="button" className="text-button" disabled={disabled} onClick={() => setOpen(false)}>Cancel</button></div>
  </form>
}
