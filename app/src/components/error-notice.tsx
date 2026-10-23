import { ApiError } from '../lib/api'
import { Button } from './ui/button'

export function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  return <div role="alert" className="notice error"><p>{error instanceof Error ? error.message : 'Could not complete the request.'}</p>
    {error instanceof ApiError && error.status === 401 ? <a href="/orders">Start a new guest workspace</a> : retry && <Button type="button" onClick={retry}>Retry</Button>}
  </div>
}
