# Email to Order

A fictional distributor demo for turning customer emails into checked, editable order drafts. Staff review and confirm each order. All prices are in EUR; stock and confirmation emails are simulated.

## Current development phase

AI-assisted drafts are implemented on `development`. Live extraction is off by default; manual entry and explicit saved examples work without a Gemini key.

- Save a fictional sample or pasted email before starting extraction.
- Extract bounded facts with Gemini, then match customers/products deterministically on the backend.
- Review every suggested product and address, resolve blockers, and confirm using the existing backend rules.
- Retry failed extraction on the same draft or continue manually. An unchanged matching sample can use clearly labelled saved values.
- Inspect the original email, validated extraction and provenance, normalized initial values, and approved values, including after confirmation.

Saved examples are never presented as AI output. Email text is preserved exactly and rendered as plain text. Live provider/project verification remains outstanding; mocked tests do not establish that a configured Gemini project works.

![AI suggestion after staff review](docs/screenshots/ai-review-desktop.png)

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

## Optional Gemini extraction

Install the backend dependencies and run migrations after pulling this change:

```sh
.venv/bin/python -m pip install -e './api[dev]'
.venv/bin/python -m alembic -c api/alembic.ini upgrade head
```

Before enabling live calls, verify the chosen model's structured-output support, free-tier eligibility, actual project quotas and billing configuration. Use the [Gemini structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output) and [current model pricing](https://ai.google.dev/gemini-api/docs/pricing). No model is selected automatically, and there is no fallback model or billing setup in the app.

Set these backend-only values in `.env`, then restart FastAPI:

```dotenv
GEMINI_API_KEY=your-key
GEMINI_MODEL=your-verified-free-tier-model
EXTRACTION_ENABLED=true
EXTRACTION_GUEST_LIMIT=5
EXTRACTION_DAILY_LIMIT=25
EXTRACTION_TIMEOUT_SECONDS=30
```

Limits may be lowered, up to the demo ceilings shown. Each provider attempt reserves allowance in a short database transaction: 5 per guest over a rolling 24 hours and 25 globally per UTC day by default. Failures, refusals and timeouts count; uncertain provider use is never refunded. Reservations survive process restarts and guest deletion. Disabled or missing configuration consumes no allowance. Application caps do not verify or replace provider quotas or billing controls.

Calls use the official Python SDK with automatic retries disabled, a 30-second default deadline (maximum 60), a 20,000-character email limit, an 8,192-token output limit and a 64,000-byte structured-response limit. Outputs have at most 50 lines. Relative dates and dates without an explicit year remain unresolved because pasted email has no trusted timestamp. Unknown units stay unknown; quantities and pack sizes are never guessed or converted.

Starting extraction sends the original email text to Google Gemini; use fictional data only. Free-tier content may be used to improve Google's products under its [current pricing and data-use terms](https://ai.google.dev/gemini-api/docs/pricing). The app stores the original email, validated facts, model/prompt/attempt identifiers and timestamp, initial suggestions and staff-approved values. It stores no duplicate raw provider response and writes no email/provider-body logs. Schema validation limits shape and authority; it cannot establish that every extracted fact is correct. Staff review remains required.

If a call fails, open the saved draft to retry or enter details manually. After a lost response, use **Reload extraction status** to recover the persisted attempt. A crashed attempt expires after its call deadline plus 15 seconds. A new attempt is allowed only after failure, on an unedited manual draft. Successful extraction initializes values once; staff saves or confirmations win over late results. Saved-example recovery is available only for an unchanged matching sample.

To disable extraction, set `EXTRACTION_ENABLED=false` and restart FastAPI. Existing drafts, manual entry and saved examples remain available. No live smoke check was performed on 23 October 2026: a key was present locally, but no model or verified free-tier project configuration was available.

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
| Extraction | `GET /api/orders/extraction-config`, `POST /api/orders/:id/extract`, `POST /api/orders/:id/saved-example` |
| Confirmation | `POST /api/orders/:id/confirm` |
| Fictional records | `GET /api/customers`, `GET /api/catalogue/products`, `GET /api/orders/samples` |
| Health / API reference | `/api/health`, `/docs` |

Two customers, saved addresses, four products and five sample scenarios remain immutable fictional fixtures. Guest sessions, drafts, editable lines and confirmed snapshots are stored in the database. FastAPI serves the built frontend and preserves JSON 404 responses for unknown API routes.

During order review, use **Add new customer** in the Customer step to save a name and email and select that customer. New customers are stored in the current guest workspace and are available for later drafts there. Review the delivery address separately. Customer creation does not send email; confirmed orders preserve the selected customer details. Run migrations after pulling this change.

## Order and workspace rules

- Every order read and write is scoped to an active guest session. Other visitors receive 404 for an order they do not own.
- An opaque HttpOnly, SameSite=Strict cookie identifies the workspace; only its hash is stored. Sessions expire 24 hours after creation. An expired session requires a new workspace and cannot reopen old orders.
- Browser mutations require a custom request header. Secrets are never exposed through Vite variables.
- Backend checks require a known customer, reviewed catalogue products, positive quantities, whole cases, a supplied and explicitly approved address, and sufficient simulated stock across all duplicate SKU lines.
- Saved address selection replaces the field only after a staff action, and resets approval. Staff must resolve any conflict with the original email.
- Partial-case lines show a backend-calculated whole-case option, including extra units. Staff must explicitly apply the correction and review the product again. **Needs customer clarification** keeps the draft blocked and appears in order history after saving.
- Quantity decisions retain the original quantity/unit, approved quantity/product and reason in the saved line and confirmed snapshot. Editing the product, quantity or unit requires a fresh decision. Original emails and initial draft values remain unchanged.
- Catalogue prices determine totals using Decimal arithmetic. Client-supplied prices are rejected. Requests are limited to 20,000 email characters, 50 lines and bounded field sizes.
- Draft saves use version checks. Unsaved edits disable confirmation; stale saves and confirmations return a conflict for review.
- Confirmation revalidates on the backend and uses a transactional state change plus a unique draft-to-order relationship. Concurrent requests and retries return one order.
- Confirmed snapshots preserve original email, initial values, approved values, prices, totals, customer details and simulated confirmation text. They are read-only through the API.

## Verification

```sh
npm --prefix app run lint
npm --prefix app test
npm --prefix app run build
.venv/bin/python -m pytest api/tests -c api/pyproject.toml
```

To run the workflow tests against a dedicated disposable PostgreSQL database:

```sh
TEST_DATABASE_URL='postgresql+psycopg://user:password@localhost/test_database' \
  .venv/bin/python -m pytest api/tests -c api/pyproject.toml
```

The test user needs permission to create and drop schemas. Each database-backed test uses an isolated schema. GitHub Actions runs frontend checks and backend tests with SQLite and PostgreSQL 16.

The 102-test backend suite covers extraction contracts, matching, SDK transport behavior, durable usage caps, failure recovery, extraction/save/confirmation races, provenance, migrations, ownership, expiration, durable drafts, version conflicts, catalogue pricing, quantities, duplicate-line stock checks, concurrent confirmation and immutable snapshots. See [verification notes](docs/verification.md) for browser scenarios and evidence.

## Remaining work and limitations

This phase is a local AI-assisted demo with deterministic provider tests and browser checks. Actual Gemini model/project verification, scheduled expired-record cleanup and public deployment are still pending. Expiration blocks access but does not yet physically delete database records. Rate limits and retention cleanup must be completed before opening the demo publicly. No email is sent, stock is not reserved, requested dates are not guaranteed, and there are no tax or shipping calculations.

A lost confirmation response can be retried safely. Draft creation is not idempotent: if a create response is lost, check Orders before creating again. No performance or time-saving claims have been measured.

Next: verify a free-tier Gemini project with a deliberate fictional-data smoke check, then complete public-demo hardening and deployment. GitHub OAuth and owner-only Resend integration remain release-two work. The full scope is in [the original plan](docs/project-plan.md).

See [the next-phase implementation plan](docs/next-phase-plan.md) for the extraction milestones, verification gates and subsequent public-demo readiness work.

## Branch workflow

`master` retains the scaffold baseline. Implement, verify and commit logical steps on `development`; review before promoting to `master`.
