Run from `api/`: `../.venv/bin/python -m alembic upgrade head`.

The initial migration creates guest sessions, drafts, editable lines, and confirmed snapshots. DATABASE_URL selects PostgreSQL; with no URL the local SQLite file is `.local/orders.db` at the repository root. Schema creation is explicit, never performed by application startup. Downgrade removes temporary order data.
