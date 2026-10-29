# Operations

Deployment and maintenance notes. For local setup, see the [README](../README.md).

## Public-access safeguards

Run migrations before starting an updated server (`.venv/bin/python -m alembic -c api/alembic.ini upgrade head`). Public limits are persisted in the database and shared across workers and restarts:

- API bodies are capped at 128 KiB before JSON parsing, including streamed requests and incorrect Content-Length headers (HTTP 413).
- All API requests, including failed and oversized requests, share a 1,200/minute global budget and a 120/minute client-address budget (HTTP 429 with Retry-After).
- New workspaces are limited to 5/hour per client address and 100/hour globally. Reusing a valid workspace does not consume a creation slot.
- Storage is capped at 1,000 retained workspaces, including expired workspaces, and 100 orders, 100 added customers and 100 added products per workspace (HTTP 409). Orders include both drafts and confirmed orders. Built-in catalogue entries and customers do not count.
- Order history returns `{items, total}` with `limit` (default 25, maximum 50), `offset` (maximum 1,000), and optional `status=draft|confirmed`. The UI paginates and filters on the server.

These ceilings can be lowered in `.env`. Database transactions serialize concurrent reservations. Rate windows start with their first request; expired rate buckets are pruned on subsequent requests. Clearing cookies does not reset address or global budgets, and rotating addresses cannot bypass global budgets or the storage ceiling. Existing records are preserved when a ceiling is reached; schedule the cleanup command below to reclaim expired storage. Limits do not retroactively remove records from an existing database that already exceeds them.

Address budgets use the ASGI connection address. The direct-server command disables proxy headers. Behind a reverse proxy, restrict direct backend access and configure Uvicorn's trusted proxy addresses explicitly; never trust arbitrary forwarded addresses. Without trusted forwarding, users behind the same proxy share its address budget.

## Expired workspace cleanup

After running migrations, run this command from the repository root using the same environment and database as the API:

```sh
cd api && ../.venv/bin/python -m src.cleanup
```

It deletes guests whose 24-hour workspace lifetime has ended, with their drafts, draft lines, confirmed orders, added customers and added products. Active workspaces are preserved. Extraction usage remains until both its rolling 24-hour guest window and UTC daily accounting window end, and its provider timeout has passed. Attempts belonging to active workspaces remain for retry idempotency. Deleting a workspace never refunds AI allowance or resets public rate budgets.

Each run prints JSON deletion counts after committing. Failures roll back the transaction and exit nonzero. Repeated or overlapping runs are safe: cleanup uses the same database locks as storage checks and AI reservations. No API server needs to be running.

On a continuously running deployment host, install an hourly cron entry with `crontab -e` as the API's service user (replace `/srv/email-to-order` with the absolute checkout path):

```cron
17 * * * * cd /srv/email-to-order/api && /srv/email-to-order/.venv/bin/python -m src.cleanup >> /srv/email-to-order/.local/cleanup.log 2>&1
```

Create the `.local` directory first and ensure the service user can write it. The command loads the root `.env`; if the API receives `DATABASE_URL` from its service environment instead, supply that same environment to cron. Monitor nonzero exits and rotate `cleanup.log` with the host's log rotation. Hourly cleanup normally removes expired workspaces within an hour; after downtime the next run catches up. This schedule must be installed on the deployment host; repository CI only runs tests against disposable databases.
