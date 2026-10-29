# Guest workspaces

Visitors receive an opaque, HttpOnly, SameSite=Strict cookie. Only its SHA-256 hash is stored. Sessions expire after 24 hours.

All order reads and writes must use the active guest dependency and scope records by guest ID. Mutation requests require `X-Requested-With: EmailToOrder` to reject cross-origin form requests. Set `COOKIE_SECURE=true` when serving over HTTPS.

See [operations](../../../docs/operations.md) for request limits and expired workspace cleanup.
