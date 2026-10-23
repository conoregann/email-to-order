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
../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
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

## Current limitations

This is a local demo. Live Gemini verification, public deployment, request rate limits and scheduled data cleanup are pending. Guest workspaces expire after 24 hours, but expired records are not yet deleted. Stock is not reserved; tax and shipping calculations are not included.

See the [project plan](docs/project-plan.md), [next-phase plan](docs/next-phase-plan.md) and [verification notes](docs/verification.md) for implementation details and remaining work.

Develop on `development`; review and verify changes before merging into `master`.
