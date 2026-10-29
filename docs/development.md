# Development

See the [README](../README.md#run-locally) for first-time setup.

## Local development

Add `--reload` to the backend command. In another terminal, run `npm --prefix app run dev` from the repository root and open the URL Vite prints. Vite forwards `/api` requests to the backend.

SQLite stores data in `.local/orders.db`. After backend updates, reinstall Python dependencies and rerun migrations.

## Configuration

Settings live in the root `.env`. See [.env.example](../.env.example) for all options.

- **PostgreSQL:** set `DATABASE_URL` and run migrations. Existing SQLite data is not copied.
- **Neon:** `neon deploy` applies `neon.ts` to the project and branch in the ignored `.neon` file, then pulls credentials into the ignored `.env`. The Python API uses the pooled `DATABASE_URL` through SQLAlchemy/Psycopg; Alembic uses `DATABASE_URL_UNPOOLED` when supplied. Run `.venv/bin/python -m alembic -c api/alembic.ini upgrade head` before starting the API. Neon hosts the database; the web application still needs its Render deployment. Use `npm run build` at the repository root to build the frontend.
- **Gemini:** disabled by default. Set `GEMINI_API_KEY`, `GEMINI_MODEL` and `EXTRACTION_ENABLED=true`, then restart. Verify model support, project quotas and billing settings first. Extraction sends email text to Gemini; use fictional data and review every suggestion. Set `EXTRACTION_ENABLED=false` to disable it.
- **HTTPS:** set `COOKIE_SECURE=true`. Keep credentials on the backend.

## Checks

Run from the repository root:

```sh
npm --prefix app run lint
npm --prefix app test
npm --prefix app run build
.venv/bin/python -m pytest api/tests -c api/pyproject.toml
```

CI runs frontend checks and backend tests on SQLite and PostgreSQL. Develop on `development`; review and verify changes before merging into `master`.

## Demo limits

The local demo is verified; see the [final readiness pass](verification.md#final-readiness-pass--29-october-2026). Live Gemini extraction passed, with project quota and billing evidence still outstanding. Public deployment is a separate remaining step. Guest workspaces expire after 24 hours; [schedule cleanup](operations.md#expired-workspace-cleanup) to delete expired records. Stock is not reserved, and tax and shipping are not calculated.
