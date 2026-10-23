import type { Customer, Product, Values } from './types'

export type ReviewStep = 0 | 1 | 2 | 3
export type ReviewProgress = { active: ReviewStep; completed: boolean[] }
type Action = { type: 'open'; step: ReviewStep } | { type: 'complete' | 'invalidate'; step: 0 | 1 | 2 } | { type: 'reset' }
export const initialProgress: ReviewProgress = { active: 0, completed: [false, false, false] }

export function availableStep(progress: ReviewProgress): ReviewStep {
  const incomplete = progress.completed.findIndex(complete => !complete)
  return (incomplete === -1 ? 3 : incomplete) as ReviewStep
}

export function reviewReducer(state: ReviewProgress, action: Action): ReviewProgress {
  if (action.type === 'reset') return initialProgress
  if (action.type === 'invalidate') return {
    active: Math.min(state.active, action.step) as ReviewStep,
    completed: state.completed.map((complete, index) => index >= action.step ? false : complete),
  }
  if (action.step > availableStep(state)) return state
  if (action.type === 'open') return { ...state, active: action.step }
  return { active: (action.step + 1) as ReviewStep, completed: state.completed.map((complete, index) => index === action.step ? true : complete) }
}

// These gates guide review. Stock, whole cases, prices and confirmation remain backend checks.
export function canContinueReview(step: ReviewStep, values: Values, customers: Customer[], products: Product[]): boolean {
  if (step === 0) return customers.some(customer => customer.id === values.customer_id)
  if (step === 1) return !!values.delivery_address.trim() && values.delivery_confirmed
  if (step === 2) return values.lines.length > 0 && values.lines.every(line =>
    products.some(product => product.sku === line.sku) && line.match_confirmed &&
    Number.isFinite(Number(line.quantity)) && Number(line.quantity) > 0 && line.quantity_unit !== 'unknown')
  return false
}
