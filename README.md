# Email to Order

A fictional distributor demo for turning customer emails into checked, editable order drafts. Staff review and confirm each order. All prices are in EUR; stock and confirmation emails are simulated.

## Current development phase

The manual workflow is implemented on `development`:

- Create a draft from a sample email or pasted text.
- Compare the original email with editable customer, address and product lines.
- Resolve product ambiguity, quantities, pack sizes and stock issues.
- Save drafts, review backend checks and confirm a valid order.
- Reopen drafts and read-only confirmed orders from history.
- View a simulated confirmation email and inspect initial versus approved values.

Samples use clearly labelled saved values, not live AI. Pasted emails start with blank order fields. The original email is preserved exactly and rendered as plain text.

![Manual order review](docs/screenshots/review-desktop.png)

## Local setup

Requires Node 22.12+ and Python 3.12+. From the repository root:

```sh
cp .env.example .env
python3 -m venv .venv
.venv/bin/python -m pip install -e './api[dev]'
.venv/bin/python -m alembic -c api/alembic.ini upgrade head
cd app
npm ci
npm run build
cd ../api
../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Open [the local app](http://127.0.0.1:8000). No AI key or external database is needed. The default database is `.local/orders.db`, excluded from Git. Migrations are explicit; application startup does not create tables.

For frontend development, run `npm run dev` from `app/` in another terminal and use the Vite URL. Vite forwards `/api` to port 8000. Use `../.venv/bin/python -m uvicorn src.main:app --reload --host 127.0.0.1` from `api/` for backend reloads.

## PostgreSQL / Neon configuration

Set `DATABASE_URL` in the root `.env`, then run the same migration command. For example:

```dotenv
DATABASE_URL=postgresql+psycopg://user:password@host/database?sslmode=require
```

Plain `postgresql://` and `postgres://` URLs are also normalized to the psycopg driver. Keep credentials on the backend. Set `COOKIE_SECURE=true` when serving over HTTPS. SQLite data is not automatically transferred when switching databases.

No Neon or Render resources have been provisioned, and no paid services have been enabled.

## Architecture and routes

```text
React + TypeScript + Vite + Tailwind
             │ same-origin /api requests
             ▼
FastAPI feature routers → Pydantic validation
             │
             ▼
SQLAlchemy → SQLite locally / PostgreSQL on Neon
             ▲
          Alembic migrations
```

| Area | Routes / responsibility |
| --- | --- |
| Frontend | `/orders`, `/orders/new`, `/orders/:id/review`, `/orders/:id/confirmed` |
| Guest session | `POST /api/auth/guest` |
| Drafts and history | `GET/POST /api/orders`, `GET/PUT /api/orders/:id` |
| Confirmation | `POST /api/orders/:id/confirm` |
| Fictional records | `GET /api/customers`, `GET /api/catalogue/products`, `GET /api/orders/samples` |
| Health / API reference | `/api/health`, `/docs` |

Two customers, saved addresses, four products and five sample scenarios remain immutable fictional fixtures. Guest sessions, drafts, editable lines and confirmed snapshots are stored in the database. FastAPI serves the built frontend and preserves JSON 404 responses for unknown API routes.

## Order and workspace rules

- Every order read and write is scoped to an active guest session. Other visitors receive 404 for an order they do not own.
- An opaque HttpOnly, SameSite=Strict cookie identifies the workspace; only its hash is stored. Sessions expire 24 hours after creation. An expired session requires a new workspace and cannot reopen old orders.
- Browser mutations require a custom request header. Secrets are never exposed through Vite variables.
- Backend checks require a known customer, reviewed catalogue products, positive quantities, whole cases, a supplied and explicitly approved address, and sufficient simulated stock across all duplicate SKU lines.
- Saved address selection replaces the field only after a staff action, and resets approval. Staff must resolve any conflict with the original email.
- Catalogue prices determine totals using Decimal arithmetic. Client-supplied prices are rejected. Requests are limited to 20,000 email characters, 50 lines and bounded field sizes.
- Draft saves use version checks. Unsaved edits disable confirmation; stale saves and confirmations return a conflict for review.
- Confirmation revalidates on the backend and uses a transactional state change plus a unique draft-to-order relationship. Concurrent requests and retries return one order.
- Confirmed snapshots preserve original email, initial values, approved values, prices, totals, customer details and simulated confirmation text. They are read-only through the API.

## Verification

```sh
npm --prefix app run lint
npm --prefix app run build
.venv/bin/python -m pytest api/tests -c api/pyproject.toml
```

To run the workflow tests against a dedicated disposable PostgreSQL database:

```sh
TEST_DATABASE_URL='postgresql+psycopg://user:password@localhost/test_database' \
  .venv/bin/python -m pytest api/tests -c api/pyproject.toml
```

The test user needs permission to create and drop schemas. Each database-backed test uses an isolated schema. GitHub Actions runs frontend checks and backend tests with SQLite and PostgreSQL 16.

The 26-test suite covers migrations, ownership, expiration, durable drafts, version conflicts, catalogue pricing, quantities, duplicate-line stock checks, concurrent confirmation and immutable snapshots. See [verification notes](docs/verification.md) for browser scenarios and evidence.

## Remaining work and limitations

This phase is a local manual demo. Live Gemini extraction, usage limits, a global extraction cap, scheduled expired-record cleanup and public deployment are still pending. Expiration blocks access but does not yet physically delete database records. Rate limits and retention cleanup must be completed before opening the demo publicly. No email is sent, stock is not reserved, requested dates are not guaranteed, and there are no tax or shipping calculations.

A lost confirmation response can be retried safely. Draft creation is not idempotent: if a create response is lost, check Orders before creating again. No performance or time-saving claims have been measured.

Next: structured Gemini extraction with ambiguity handling and an explicit saved-example fallback. GitHub OAuth and owner-only Resend integration remain release-two work. The full scope is in [the original plan](docs/project-plan.md).

## Branch workflow

`master` retains the scaffold baseline. Implement, verify and commit logical steps on `development`; review before promoting to `master`.
