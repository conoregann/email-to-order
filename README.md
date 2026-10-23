# Email to Order

A fictional distributor demo that will turn customer emails into checked, editable order drafts. Staff review and confirm each order. Currency: EUR.

## Current iteration

The initial `master` commit provides the React/TypeScript/Vite frontend, Tailwind and a shadcn-style Button primitive, FastAPI feature routers, configuration, optional SQLAlchemy wiring, CI and route tests. `development` is branched from that foundation for seed data and subsequent iterations.

Frontend routes: `/orders`, `/orders/new`, `/orders/:orderId/review`, `/orders/:orderId/confirmed`. Review and confirmation are explicitly labelled placeholders. API routes are under `/api`; inspect `/docs` for OpenAPI.

## Local setup

Requires Node 22.12+ and Python 3.12+. Run from the repository root:

```sh
cp .env.example .env
python3 -m venv .venv
.venv/bin/python -m pip install -e './api[dev]'
cd api
../.venv/bin/uvicorn src.main:app --reload --host 127.0.0.1
```

In another terminal:

```sh
cd app
npm ci
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). Vite forwards `/api` to port 8000. No database or AI key is needed for this iteration. Keep backend secrets out of Vite variables.

## Checks

```sh
cd app
npm run lint
npm run build
cd ../api
../.venv/bin/python -m pytest
```

After building the frontend, FastAPI serves `app/dist` and supports direct navigation to frontend routes. Unknown `/api` routes still return JSON 404 responses. Run Uvicorn from `api/` as above, without `--reload` for a production process.

## Development plan

1. Fictional products, customers, saved addresses and sample emails.
2. Manual drafts, deterministic validation, correction audit trail and idempotent confirmation.
3. Gemini extraction, ambiguity handling, saved-example fallback and retries.
4. Guest ownership enforcement, usage caps and expiration before public order persistence.
5. Workflow and access tests, then Render/Neon deployment with no paid upgrades.
6. GitHub login and owner-only Resend integration in release two.

No orders are persisted, no AI calls occur, and no emails are sent yet. PostgreSQL migrations and external credentials are deferred until the persistence iteration. Deployment, live URL and screenshots are pending. See [the original project plan](docs/project-plan.md) for full rules and completion criteria.

## Branch workflow

Keep the baseline on `master`. Continue implementation on `development`; validate and review changes before promoting them to `master`.
