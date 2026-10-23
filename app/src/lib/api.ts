export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}
async function request<T>(path: string, options: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { credentials: 'same-origin', ...options })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    const message = typeof detail === 'string' ? detail : detail?.message ?? (Array.isArray(detail) ? 'Some fields are invalid. Check quantities and field lengths.' : `Request failed (${response.status}). Please retry.`)
    throw new ApiError(message, response.status)
  }
  return response.json() as Promise<T>
}
export function getJson<T>(path: string, signal?: AbortSignal) { return request<T>(path, { signal }) }
export function sendJson<T>(path: string, method: 'POST' | 'PUT', body: unknown) {
  return request<T>(path, { method, headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'EmailToOrder' }, body: JSON.stringify(body) })
}
let starting: Promise<{ expires_at: number }> | null = null
export function startWorkspace() {
  starting ??= sendJson<{ expires_at: number }>('/auth/guest', 'POST', {}).finally(() => { starting = null })
  return starting
}
