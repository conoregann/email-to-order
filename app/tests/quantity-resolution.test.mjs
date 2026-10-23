import test from 'node:test'
import assert from 'node:assert/strict'
import { editOrderLine, quantityRequest } from '../src/lib/quantity-resolution.ts'
import { canContinueReview } from '../src/lib/review-flow.ts'

const line = { requested_product: 'cups', sku: 'CUP-12OZ-50', quantity: '75', quantity_unit: 'unit', match_confirmed: true }
const decision = { ...quantityRequest(line), status: 'adjusted', reason: 'Customer agreed to 100 cups.', approved_quantity: '2', approved_unit: 'case', approved_sku: line.sku }
const approved = { ...line, quantity: '2', quantity_unit: 'case', quantity_resolution: decision }

test('changing quantity resets product approval and preserves the first request', () => {
  const edited = editOrderLine(line, { quantity: '100' })
  assert.equal(edited.match_confirmed, false)
  assert.equal(edited.quantity_resolution.status, 'unresolved')
  assert.equal(edited.quantity_resolution.requested_quantity, '75')
  const again = editOrderLine(edited, { quantity: '150' })
  assert.equal(again.quantity_resolution.requested_quantity, '75')
  assert.equal(again.quantity_resolution.requested_unit, 'unit')
})

test('explicit whole-case approval is retained while product approval is reset', () => {
  const edited = editOrderLine(line, { quantity: '2', quantity_unit: 'case', quantity_resolution: decision })
  assert.equal(edited.match_confirmed, false)
  assert.deepEqual(edited.quantity_resolution, decision)
})

test('product, quantity and unit edits invalidate an approved quantity decision', () => {
  for (const patch of [{ sku: 'OAT-1L-06' }, { quantity: '3' }, { quantity_unit: 'unit' }]) {
    const edited = editOrderLine(approved, patch)
    assert.equal(edited.quantity_resolution.status, 'unresolved')
    assert.equal(edited.quantity_resolution.approved_quantity, null)
    assert.equal(edited.match_confirmed, false)
    assert.equal(edited.quantity_resolution.requested_quantity, '75')
  }
})

test('entering a new line does not require a correction decision', () => {
  const blank = { ...line, sku: null, quantity: null, quantity_unit: 'unknown', match_confirmed: false }
  const typed = editOrderLine(blank, { quantity: '2' })
  assert.equal(editOrderLine(typed, { quantity_unit: 'case' }).quantity_resolution, undefined)
})

test('clarification and unresolved changes cannot pass product review', () => {
  const values = { lines: [approved] }
  const products = [{ sku: line.sku }]
  assert.equal(canContinueReview(2, values, [], products), true)
  for (const status of ['unresolved', 'needs_clarification']) {
    assert.equal(canContinueReview(2, { lines: [{ ...approved, quantity_resolution: { ...decision, status } }] }, [], products), false)
  }
  assert.equal(canContinueReview(2, { lines: [{ ...approved, quantity_resolution: { ...decision, reason: '' } }] }, [], products), false)
})
