import type { Line, QuantityResolution } from './types'

export function quantityRequest(line: Line): QuantityResolution {
  return line.quantity_resolution ?? { requested_quantity: line.quantity, requested_unit: line.quantity_unit, status: 'unresolved', reason: '', approved_quantity: null, approved_unit: 'unknown', approved_sku: null }
}

export function editOrderLine(line: Line, patch: Partial<Line>): Line {
  const changed = (['sku', 'quantity', 'quantity_unit'] as const).some(key => key in patch && patch[key] !== line[key])
  const updated = { ...line, ...patch }
  if (changed) {
    updated.match_confirmed = false
    if (!('quantity_resolution' in patch) && (line.quantity_resolution || (line.quantity !== null && line.quantity_unit !== 'unknown' && line.sku && ('quantity' in patch || 'quantity_unit' in patch)))) {
      updated.quantity_resolution = { ...quantityRequest(line), status: 'unresolved', approved_quantity: null, approved_unit: 'unknown', approved_sku: null }
    }
  }
  return updated
}
