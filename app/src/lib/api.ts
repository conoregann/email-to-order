export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api${path}`, { signal })
  if (!response.ok) throw new Error(`Request failed (${response.status}). Please retry.`)
  return response.json() as Promise<T>
}
