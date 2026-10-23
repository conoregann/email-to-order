import test from 'node:test'
import assert from 'node:assert/strict'
import { availableStep, canContinueReview, initialProgress, reviewReducer } from '../src/lib/review-flow.ts'

const customers = [{ id: 'customer-1' }]
const products = [{ sku: 'SKU-1', stock_cases: 1 }]
const values = { customer_id: 'customer-1', delivery_address: '12 Quay Street', delivery_confirmed: true, lines: [{ sku: 'SKU-1', quantity: '2', quantity_unit: 'case', match_confirmed: true }] }
const completed = [0, 1, 2].reduce((state, step) => reviewReducer(state, { type: 'complete', step }), initialProgress)

test('future sections cannot open or complete before preceding reviews', () => {
  assert.equal(reviewReducer(initialProgress, { type: 'open', step: 3 }), initialProgress)
  assert.equal(reviewReducer(initialProgress, { type: 'complete', step: 2 }), initialProgress)
})
test('completing each review reveals the next section', () => {
  assert.deepEqual(completed, { active: 3, completed: [true, true, true] })
  assert.equal(availableStep(completed), 3)
  assert.deepEqual(initialProgress.completed, [false, false, false])
})
test('editing customer invalidates delivery and product reviews', () => {
  assert.deepEqual(reviewReducer(completed, { type: 'invalidate', step: 0 }), initialProgress)
})
test('editing delivery retains customer approval and reopens delivery', () => {
  assert.deepEqual(reviewReducer(completed, { type: 'invalidate', step: 1 }), { active: 1, completed: [true, false, false] })
})
test('editing products invalidates final checks without resetting customer or delivery', () => {
  const updated = reviewReducer(completed, { type: 'invalidate', step: 2 })
  assert.deepEqual(updated, { active: 2, completed: [true, true, false] })
  assert.equal(reviewReducer(updated, { type: 'open', step: 3 }), updated)
})
test('reopening an unchanged section retains later reviews', () => {
  assert.deepEqual(reviewReducer(completed, { type: 'open', step: 0 }), { active: 0, completed: [true, true, true] })
})
test('new extraction results require a fresh review', () => {
  assert.deepEqual(reviewReducer(completed, { type: 'reset' }), initialProgress)
})
test('customer must be a known record', () => {
  assert.equal(canContinueReview(0, values, customers, products), true)
  assert.equal(canContinueReview(0, { ...values, customer_id: 'unknown' }, customers, products), false)
})
test('delivery needs both an address and explicit approval', () => {
  assert.equal(canContinueReview(1, values, customers, products), true)
  assert.equal(canContinueReview(1, { ...values, delivery_confirmed: false }, customers, products), false)
  assert.equal(canContinueReview(1, { ...values, delivery_address: '  ' }, customers, products), false)
})
test('every product requires a known SKU, review, positive quantity and known unit', () => {
  assert.equal(canContinueReview(2, values, customers, products), true)
  assert.equal(canContinueReview(2, { ...values, lines: [] }, customers, products), false)
  for (const patch of [{ sku: null }, { sku: 'unknown' }, { match_confirmed: false }, { quantity: null }, { quantity: '0' }, { quantity: '-1' }, { quantity: 'Infinity' }, { quantity: 'x' }, { quantity_unit: 'unknown' }]) {
    assert.equal(canContinueReview(2, { ...values, lines: [values.lines[0], { ...values.lines[0], ...patch }] }, customers, products), false)
  }
})
test('continuation never confirms an order or substitutes for backend stock checks', () => {
  assert.equal(canContinueReview(3, values, customers, products), false)
  assert.equal(canContinueReview(2, values, customers, products), true)
})
