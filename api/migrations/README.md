# Database migrations

From the repository root, after installing backend dependencies:

```sh
.venv/bin/python -m alembic -c api/alembic.ini upgrade head
```

Run this before starting the API and after pulling database changes. Application startup does not create or migrate the schema.

SQLite defaults to `.local/orders.db` at the repository root. Set `DATABASE_URL` in the root `.env` to use PostgreSQL. Migrations update the selected database; they do not copy data between databases. Downgrades can delete data.
