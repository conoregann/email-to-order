# Email to Order

A distributor demo that turns customer emails into editable order drafts. Staff review customer details, products, quantities and delivery information before confirming an order.

## What it does

- Create drafts from pasted emails, fictional samples or optional Gemini extraction.
- Validate products, pack sizes, quantities, prices and simulated stock.
- Add customers and products within a guest workspace.
- Save drafts, review corrections and confirm orders without duplicates on retry.
- Keep the original email and approved order details for reference.

All prices are in EUR. Stock and confirmation emails are simulated; no emails are sent.

## Run locally

Requires **Node.js 22.12+** and **Python 3.12+**. From the repository root on macOS or Linux:

```sh
cp .env.example .env
python3 -m venv .venv
.venv/bin/python -m pip install -e './api[dev]'
.venv/bin/python -m alembic -c api/alembic.ini upgrade head
npm --prefix app ci
npm --prefix app run build
cd api
../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Open [the app](http://127.0.0.1:8000) or [API documentation](http://127.0.0.1:8000/docs).

SQLite stores local data in `.local/orders.db`. No external database or AI key is required. After pulling backend updates, refresh Python dependencies and run migrations again.

For development, add `--reload` to the backend command and run `npm --prefix app run dev` from the repository root in another terminal. Vite forwards `/api` requests to port 8000.

## Configuration

Backend settings are in the root `.env`; see [.env.example](.env.example) for available options. Keep credentials out of frontend environment variables.

- **Database:** SQLite by default. Set `DATABASE_URL` to use PostgreSQL, then run migrations. Existing SQLite data is not transferred automatically.
- **AI extraction:** Disabled by default. Set `GEMINI_API_KEY`, `GEMINI_MODEL` and `EXTRACTION_ENABLED=true`, then restart the backend. Verify the model's capabilities, project quotas and billing settings first. Extraction sends email text to Gemini; use fictional data only. Staff review is required.
- **HTTPS:** Set `COOKIE_SECURE=true` when serving over HTTPS.

## Stack

React, TypeScript, Vite and Tailwind CSS in `app/`; FastAPI, Pydantic, SQLAlchemy and Alembic in `api/`. FastAPI serves the built frontend and API from one origin.

## Checks

Run from the repository root:

```sh
npm --prefix app run lint
npm --prefix app test
npm --prefix app run build
.venv/bin/python -m pytest api/tests -c api/pyproject.toml
```

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

## Current limitations

This is a local demo. Live Gemini verification and public deployment are pending. Guest workspaces expire after 24 hours; operators must install the cleanup schedule above to delete expired records. Stock is not reserved; tax and shipping calculations are not included.

See the [project plan](docs/project-plan.md), [next-phase plan](docs/next-phase-plan.md) and [verification notes](docs/verification.md) for implementation details and remaining work.

Develop on `development`; review and verify changes before merging into `master`.
