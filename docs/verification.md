# Manual workflow verification — 23 October 2026

## Automated checks

- Frontend lint and production build passed.
- 26 backend tests passed with the default SQLite configuration.
- The same suite passed with the workflow fixtures running against a temporary PostgreSQL 14 instance. CI is configured to repeat against PostgreSQL 16.
- Alembic upgrade/downgrade/upgrade passed; migrated SQLite schema matches SQLAlchemy metadata.
- Eight concurrent confirmation attempts returned one confirmed order and one order number.
- Guest isolation, session expiration, repeated confirmation, stale saves, immutable approved values and persistence across application instances passed.

The installed Starlette emits a deprecation warning for its httpx-based TestClient; it does not affect the test results.

## Real-browser checks

Playwright exercised the built frontend served by FastAPI:

1. Created an ambiguous oat-milk sample, selected an exact product, approved its delivery address and saved. Backend checks passed with a total of EUR 41.40.
2. Confirmed the order, reopened it from history and reloaded its direct URL.
3. Opened another visitor's order URL in a separate browser context and received Order not found. That visitor's history was empty.
4. Loaded a missing-address sample and selected a saved address. Selection did not silently approve the address.
5. Simulated a failed save, checked that edits were retained, and saved successfully on retry.
6. Allowed confirmation to commit on the server, then deliberately lost its browser response. Retrying returned the existing order number.
7. Corrected 75 cups to 100 units in the pack-size sample, resulting in two whole cases and EUR 11.00.
8. Checked desktop and 390px-wide mobile layouts, including page overflow.

Screenshots were visually inspected:

- [Desktop review](screenshots/review-desktop.png)
- [Desktop confirmation](screenshots/confirmed-desktop.png)
- [Mobile review](screenshots/review-mobile.png)

Browser fault injection was temporary and is not part of application code. No live AI, Neon account, public hosting, or email delivery was used.
