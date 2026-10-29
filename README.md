# Email to Order

Turn customer emails into order drafts. Review the details, fix any issues and confirm the order.

**Paste email → Create draft → Review → Confirm**

Use fictional samples, enter details manually or try optional Gemini extraction.

> Local demo for distributors. Stock and confirmation emails are simulated; no emails are sent.

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

Open [the app](http://127.0.0.1:8000). No AI key or external database needed.

## Configuration

SQLite works out of the box. Gemini is off by default. See [configuration and development](docs/development.md) for settings, AI setup and test commands.

## Built with

**React + TypeScript** frontend · **FastAPI** backend · **SQLite / PostgreSQL** database

[Operations](docs/operations.md) · [Verification](docs/verification.md) · [API docs](http://127.0.0.1:8000/docs)
