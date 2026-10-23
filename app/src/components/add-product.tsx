import { useState } from 'react'
import type { FormEvent } from 'react'
import { sendJson } from '../lib/api'
import type { Product } from '../lib/types'
import { ErrorNotice } from './error-notice'
import { Button } from './ui/button'

export function AddProduct({ index, name, disabled, onCreated, onBusy }: { index: number; name: string; disabled: boolean; onCreated: (product: Product) => void; onBusy: (busy: boolean) => void }) {
  const [open, setOpen] = useState(false)
  const [sku, setSku] = useState('')
  const [productName, setProductName] = useState(name)
  const [packSize, setPackSize] = useState('')
  const [price, setPrice] = useState('')
  const [stock, setStock] = useState('')
  const [error, setError] = useState<unknown>(null)
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (disabled) return
    onBusy(true); setError(null)
    try {
      const product = await sendJson<Product>('/catalogue/products', 'POST', { sku, name: productName, pack_size: Number(packSize), price, stock_cases: Number(stock) })
      onCreated(product); setOpen(false)
    } catch (error) { setError(error) } finally { onBusy(false) }
  }
  if (!open) return <button type="button" className="text-button" disabled={disabled} onClick={() => { setProductName(name); setOpen(true) }}>Add new product</button>
  return <form onSubmit={create} aria-label={`Add new product for line ${index + 1}`}>
    <p className="form-help">Save a product in this workspace. Enter the pack size, price and simulated stock; check these details before approving the order.</p>
    <label htmlFor={`new-product-name-${index}`}>Product name</label><input id={`new-product-name-${index}`} required maxLength={300} value={productName} disabled={disabled} onChange={event => setProductName(event.target.value)} autoFocus />
    <label htmlFor={`new-product-sku-${index}`}>SKU</label><input id={`new-product-sku-${index}`} required maxLength={80} pattern="[A-Za-z0-9][A-Za-z0-9._\-]*" title="Use letters, numbers, dots, underscores or hyphens." value={sku} disabled={disabled} onChange={event => setSku(event.target.value)} />
    <label htmlFor={`new-product-pack-${index}`}>Units per case</label><input id={`new-product-pack-${index}`} type="number" required min="1" max="1000000" step="1" value={packSize} disabled={disabled} onChange={event => setPackSize(event.target.value)} />
    <label htmlFor={`new-product-price-${index}`}>Price per case (EUR)</label><input id={`new-product-price-${index}`} type="number" required min="0.01" max="9999999999.99" step="0.01" value={price} disabled={disabled} onChange={event => setPrice(event.target.value)} />
    <label htmlFor={`new-product-stock-${index}`}>Simulated stock (cases)</label><input id={`new-product-stock-${index}`} type="number" required min="0" max="1000000" step="1" value={stock} disabled={disabled} onChange={event => setStock(event.target.value)} />
    {error != null && <ErrorNotice error={error} />}
    <div className="actions"><Button type="submit" disabled={disabled || !productName.trim() || !sku.trim() || !packSize || !price || !stock}>Save and select product</Button><button type="button" className="text-button" disabled={disabled} onClick={() => setOpen(false)}>Cancel</button></div>
  </form>
}
