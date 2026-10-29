# Verification records

These dated records describe earlier milestones. Test counts and remaining-work statements apply to those runs. For current setup and implemented safeguards, see the [README](../README.md) and [operations guide](operations.md).

# AI-assisted draft verification — 23 October 2026

## Results

- Frontend lint and production build passed.
- All 85 backend tests passed on SQLite and a disposable PostgreSQL 14.17 instance. Existing CI repeats the suite on SQLite and PostgreSQL 16; this local run does not establish a remote CI result.
- Migration upgrade/downgrade/upgrade and model alignment passed on both databases. Saved-example drafts and confirmed snapshots remained readable across the extraction migration.
- The local default SQLite database was migrated to head (`0002`).
- Provider tests use no network/key: they cover the bounded schema, unknown/invalid facts, dates, prohibited fields, all five samples, unknown/conflicting identities, conflicting addresses, fractional cases, duplicate stock and injection-like text.
- Adapter tests exercise the actual Google Gen AI SDK 1.75.0 through a mocked HTTP transport. Structured schema transmission, one request on 429/503, output bounds, refusal, malformed JSON, safe error translation and the total call deadline passed.
- Twelve concurrent reservations could not exceed either guest or global limits. Attempts survive new sessions and failed calls; guest deletion did not refund global allowance.
- Extraction tests passed for ownership, expired guests, required browser headers, duplicate attempts, failed-attempt retries, lost responses, crashed-attempt expiry, stale versions, late results, simultaneous staff saves and confirmation, immutable provenance and repeated confirmation.

Python 3.14.7 was used locally. Starlette's TestClient and the installed Google SDK emit deprecation warnings; neither affects the results. CI uses Python 3.12.

## Browser checks

Playwright exercised the production frontend served by FastAPI, with a temporary backend-only fictional provider and separate disabled/no-key instance. The temporary provider, database and browser fault injection were outside application code. Its model label was `fictional-browser-model`; it was not a Gemini model or live extraction result.

1. Extracted the straightforward sample, checked that product/address approvals were false, explicitly approved them, saved and confirmed at EUR 27.60.
2. Extracted ambiguous oat milk, verified both candidates and no selected SKU, selected the barista product, approved the address and saved at EUR 41.40.
3. Extracted a missing-address sample, verified the address remained empty, and selected a saved address without automatic approval.
4. Verified 75 individual cups stayed 75 units, then corrected to 100 units, reviewed the product/address and saved at EUR 11.00. A failed save retained the delivery-instruction edit, which saved on retry.
5. Simulated a provider timeout and retried on the same draft ID. The original HTML-like email remained exact plain text and did not execute. Arbitrary pasted text offered no unrelated saved example.
6. Exhausted the actual five-attempt guest allowance and verified the quota message retained a link to the saved manual draft.
7. Lost the browser extraction response after the server call. Opened the saved draft while its request was still running, then used **Reload extraction status** to recover the completed AI suggestion and quantity without another provider call.
8. Ran without a key/model and with extraction disabled: the live action was absent, saved examples were labelled as stored values, and manual pasted-text drafts had blank fields.
9. Inspected desktop (1440px) and mobile (390px) review screenshots and verified no horizontal page overflow.

Evidence, visually inspected:

- [AI-assisted desktop review](screenshots/ai-review-desktop.png)
- [AI-assisted mobile review](screenshots/ai-review-mobile.png)

## Live integration gate — outstanding

No live Gemini smoke check was performed. Local configuration had a key, but no explicit model, enabled flag or verified project free-tier/quotas/billing setup. The key was not printed or used. Model support and pricing documentation were checked; that cannot establish account/project eligibility.

Before enabling: verify structured-output support and free-tier eligibility for the selected model in the actual project, verify quotas and billing/overage settings without enabling paid services, lower application limits if necessary, then deliberately extract fictional text once. Record the actual model identifier, date, outcome, observed allowance consumption and successful staff review/confirmation here. Do not treat mocked tests as live verification.

See [setup, limits and data handling](../README.md#configuration), [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output) and [model pricing/data use](https://ai.google.dev/gemini-api/docs/pricing). Free-tier content may be used to improve Google's products; keep demo text fictional.

## Remaining public-demo work

The implementation phase's automated/browser checks pass; live integration verification remains open. Physical retention cleanup, pre-parse body limits, API/session creation rate limits, bounded storage/history and public deployment are still pending. Extraction can be disabled with `EXTRACTION_ENABLED=false` and an API restart while retaining manual and saved-example access. No hosting, billing upgrades, real inbox data or real sending were enabled.

---

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


## Quantity-resolution milestone — 23 October 2026

- All 102 backend tests passed on SQLite; frontend lint, all 16 frontend tests and the production build passed. PostgreSQL was not rerun for this milestone. No migration is required: optional resolution metadata is stored in the existing line JSON; older lines and confirmed snapshots remain readable.
- Backend tests cover exact multiples, fractional cases/units, unknown units/products, positive-quantity requirements, whole-case suggestions, stock limits, stale approval decisions, authenticated/nonmutating previews, persisted clarification and immutable confirmed resolution records.
- Frontend tests cover preserving the first quantity request, resetting product approval on edits, retaining an explicit whole-case decision, invalidating decisions after product/quantity/unit edits, normal entry of new lines, and preventing unresolved decisions from passing product review.
- Browser verification used the real built frontend and API with an isolated SQLite database, live extraction disabled and the fictional 75-cup sample. At desktop width, the product step displayed 75 units requested, 50 per case, 2 cases/100 units and 25 extra.
- Marked the sample **Needs customer clarification**, saved it, verified **Needs clarification** in order history and reopened it. The pending decision persisted, with product approval and continuation disabled.
- At 390px mobile width, entered a reason, explicitly used 2 cases/100 units, verified product approval reset, approved the product, saved, passed validation and confirmed for EUR 11.00. Automated API tests also verify the original 75-unit request and resolution reason remain in the confirmed snapshot.

Reproduce: select **Quantity and pack size**, create the saved-example draft, review customer/delivery, and open Products. Either save a clarification decision or record a note and use the whole-case option. Recheck the product before saving and confirming. For a manually entered corrected quantity, add a reason and use **Approve quantity change**.

Desktop evidence: [quantity-resolution panel](screenshots/quantity-resolution-desktop.png).
