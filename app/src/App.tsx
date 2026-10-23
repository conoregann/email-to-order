import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import { WorkspaceLayout } from './components/workspace-layout'
import { NewOrder } from './pages/new-order'
import { Orders } from './pages/orders'
import { ReviewOrder } from './pages/review-order'
import { ConfirmedOrder } from './pages/confirmed-order'

export default function App() {
  return <BrowserRouter><Routes><Route element={<WorkspaceLayout />}><Route index element={<Navigate to="/orders" replace />} /><Route path="orders" element={<Orders />} /><Route path="orders/new" element={<NewOrder />} /><Route path="orders/:orderId/review" element={<ReviewOrder />} /><Route path="orders/:orderId/confirmed" element={<ConfirmedOrder />} /><Route path="*" element={<section><h1>Page not found</h1><Link to="/orders">Back to orders</Link></section>} /></Route></Routes></BrowserRouter>
}
