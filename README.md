# Email to Order

Turn customer emails into editable order drafts. Review the customer, products, quantities and delivery details, then confirm the order.

A demo for distributors using fictional data. Prices are in EUR; stock and confirmation emails are simulated. No emails are sent.

## How it works

1. Choose a sample email or paste your own text.
2. Create a draft manually, from a saved example or with optional Gemini extraction.
3. Review suggestions, correct details and resolve validation issues.
4. Confirm the order and view it in order history.

You can add customers and products in your guest workspace. The original email and approved order details are kept for reference. Retrying confirmation does not create a duplicate order.

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

Open [the app](http://127.0.0.1:8000) or [API docs](http://127.0.0.1:8000/docs).

No AI key or external database is needed. SQLite stores data in `.local/orders.db`. After backend updates, reinstall Python dependencies and rerun migrations.

For development, add `--reload` to the server command. In another terminal, run `npm --prefix app run dev` from the repository root and open the URL Vite prints. Vite forwards `/api` requests to the backend.

## Configuration

Settings live in the root `.env`. See [.env.example](.env.example) for all options.

- **PostgreSQL:** set `DATABASE_URL` and run migrations. Existing SQLite data is not copied.
- **Gemini:** disabled by default. Set `GEMINI_API_KEY`, `GEMINI_MODEL` and `EXTRACTION_ENABLED=true`, then restart. Verify model support, project quotas and billing settings first. Extraction sends email text to Gemini; use fictional data and review every suggestion. Set `EXTRACTION_ENABLED=false` to disable it.
- **HTTPS:** set `COOKIE_SECURE=true`. Keep credentials on the backend.

## Repository

| Path | Contents |
| --- | --- |
| `app/` | React, TypeScript, Vite and Tailwind CSS frontend |
| `api/src/` | FastAPI backend, validation and Gemini integration |
| `api/migrations/` | Alembic database migrations |
| `api/tests/`, `app/tests/` | Backend and frontend tests |
| `docs/` | Operations, verification records and archived plans |

FastAPI serves the built frontend and API from one origin.

## Checks

Run from the repository root:

```sh
npm --prefix app run lint
npm --prefix app test
npm --prefix app run build
.venv/bin/python -m pytest api/tests -c api/pyproject.toml
```

CI runs frontend checks and backend tests on SQLite and PostgreSQL. Develop on `development`; review and verify changes before merging into `master`.

## Status and limits

Local demo. Live Gemini verification and public deployment are pending. Guest workspaces expire after 24 hours; [schedule cleanup](docs/operations.md#expired-workspace-cleanup) to delete expired records. Stock is not reserved, and tax and shipping are not calculated.

See [operations](docs/operations.md) for public limits and deployment details, [verification records](docs/verification.md) for prior checks, and [archived plans](docs/archive/) for the original scope and implementation history.
