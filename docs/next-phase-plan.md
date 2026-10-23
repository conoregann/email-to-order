# Next phase: AI-assisted order drafts

Planning baseline: 23 October 2026, `development` at `35d6ab6`.

## Execution record — 23 October 2026

Steps 1–5 are implemented and committed on `development`. Step 6 automated and browser checks
pass: 85 tests on SQLite and disposable PostgreSQL 14, frontend lint/build, and desktop/mobile
checks with a temporary fictional provider. See [verification results](verification.md).

The live integration gate remains open: no model was configured and the actual Gemini
project's free-tier eligibility, quotas and billing configuration were not verified. Extraction
remains disabled. A deliberate fictional-data live smoke check is still required before
calling the live integration verified. Public-demo readiness and deployment below remain pending.

The tables and implementation sequence below describe the original planning baseline.

## Goal and assumptions

Complete build-plan step 3: a visitor can extract a sample or pasted email into an editable draft, resolve uncertain details, and confirm it using the existing backend checks. Extraction failures must leave the email available for retry or manual entry. The app must remain useful without an AI key.

This is an implementation plan, not a record of completed AI work. Continue on `development` and keep changes limited to extraction and the controls needed to use it safely. Public launch follows in a separate phase. GitHub login and Resend remain release-two work.

## What already exists

| Area | Repository evidence | Status |
| --- | --- | --- |
| Fictional data | Catalogue, customer and sample fixtures | Complete |
| Manual workflow | Draft creation/editing, validation, confirmation and history | Complete |
| Review safeguards | Explicit product/address approval, version checks, immutable snapshots | Complete |
| Guest workspaces | Cookie sessions, ownership checks and 24-hour access expiry | Complete |
| Verification | 26 backend tests, SQLite/PostgreSQL CI and documented browser checks | Existing baseline; rerun before implementation |
| AI extraction | API-key setting only; samples use saved values | Next |
| Public hardening | Usage limits and physical record cleanup | Pending |
| Hosting | No provisioned Neon or Render resources | Pending |

Do not rebuild the manual workflow or move catalogue pricing, stock checks or confirmation rules into the model.

## Implementation sequence

### 1. Define and test the extraction contract

- Add a bounded Pydantic extraction schema under `api/src/integrations/`. Extract customer name/email, delivery instructions, requested date, and product descriptions, explicit SKUs, quantities and units. Preserve source wording where it matters.
- Keep unknown values empty. Represent unclear units as `unknown`. Do not infer a relative delivery date without a reliable date for the source email; the current pasted-text input has no trusted sent timestamp.
- Exclude prices, stock, approval flags and confirmation actions from model authority. Reject unexpected fields and oversized output.
- Store the validated extraction separately from normalized `initial_values`, with model identifier, prompt version and timestamp. Preserve both through confirmation; staff edits must change neither. Retain no duplicate raw provider response or email logs.
- Add a migration only for the extraction state/metadata and usage records needed by this plan; preserve existing manual and saved-example drafts.

Verify: schema tests cover missing fields, invalid dates/numbers, excessive lines and prohibited fields; migration upgrade/downgrade and legacy-draft reads pass on both databases.

Suggested commit: `feat: define validated extraction records and draft provenance`.

### 2. Add deterministic matching

- Normalize extracted facts into the existing `DraftValues` contract in backend code.
- Match products using explicit SKUs, exact names and existing aliases, ignoring case and surrounding whitespace. Keep multiple candidates unresolved; contradictory SKU/name evidence requires review. Unknown products remain unselected.
- Match customers only from uniquely matching recorded names/emails. Conflicting or unidentified customers remain unselected.
- Leave all AI-derived product approvals and delivery approval false, including exact matches. Reuse existing candidate display and validation blockers.
- Preserve delivery instructions from the email. Offer saved addresses through the existing staff selection flow; do not use a saved address to fill a missing extraction automatically.
- Preserve quantities and units without rounding, guessing pack sizes or silently converting to cases. Run the existing validator for stock, packs and totals.

Verify: fixture tests cover exact SKU, unique alias, ambiguous oat milk, unknown product/customer, conflicting identity, missing/conflicting address, unspecified units, partial cases and duplicate-line stock totals.

Suggested commit: `feat: map extracted facts to reviewable order suggestions`.

### 3. Add budget controls and the Gemini adapter

- Add a small Gemini client in `api/src/integrations/` using the official Python SDK and structured output. Keep prompts and provider calls on the backend. Email content is untrusted data; enable no tools or external actions.
- Require explicit model configuration and an enabled extraction flag; default live extraction to off. Verify the selected model's structured-output support and free-tier eligibility in the actual project before enabling it. Do not configure a paid fallback or enable billing.
- Bound input, output tokens and call duration. Disable automatic SDK retries; a deliberate user retry is a separately counted provider attempt.
- Before every provider attempt, atomically reserve database-backed usage against both a guest limit and a global UTC-day cap. Count failed/time-out attempts conservatively; do not refund uncertain provider usage. Proposed local-demo defaults: 5 attempts per guest per 24 hours and 25 globally per UTC day, lowered if project quotas require it.
- Reject excess calls before contacting Gemini. Counters must survive process restarts and concurrent requests. Disabling extraction or missing configuration must not consume allowance.
- Translate missing configuration, quota exhaustion, timeouts, refusal, invalid output and provider errors into stable application errors without exposing secrets or provider response bodies.

Verify: mocked provider tests prove no call occurs when disabled/over budget; concurrent reservations cannot exceed either cap; timeout/malformed/refused responses fail safely. CI requires no Gemini key or network access.

Suggested commit: `feat: add bounded Gemini extraction with durable usage caps`.

### 4. Connect extraction to durable drafts

- Create a blank manual draft first using the existing endpoint, then extract against its ID through a new guest-owned mutation such as `POST /api/orders/{id}/extract`. Return the draft ID before the slower provider operation so failures do not lose the email.
- Persist extraction status (`not_started`, `running`, `succeeded`, `failed`) and an attempt identifier. A duplicate request for the same attempt must return its existing status/result without another provider call; allow a new attempt only after failure.
- Use a draft-version precondition and conditional writes. Reject extraction into confirmed, edited or already successfully extracted drafts. If a save or confirmation wins while extraction is running, discard the late result rather than overwriting staff work.
- Record the running attempt and reserve usage in a short transaction before the network call. Use a bounded attempt expiry so a crashed process does not leave a draft permanently running. No background queue is needed for this phase.
- Successful extraction initializes the draft once, preserves extraction provenance and runs existing backend validation. Failed extraction leaves a usable manual draft and preserves the original email exactly.
- Carry metadata into the immutable confirmed snapshot. Keep existing confirmation idempotency and ownership checks intact.

Verify: foreign/expired guests are rejected; repeated attempts, lost responses, crashes, late responses, stale versions and simultaneous staff saves cannot cause duplicate calls for an attempt or overwrite edits. Reconfirmation still returns one order.

Suggested commit: `feat: apply extraction safely to owned versioned drafts`.

### 5. Complete the UI and failure recovery

- On New order, offer live extraction when configured, manual entry, and explicit saved examples for the existing samples. Saved values must never be presented as live AI output.
- Preserve the created draft ID if extraction fails. Offer retry on that same draft, manual review, or a clearly labelled saved example. A saved example is available only for its unchanged matching sample; arbitrary pasted emails must not receive unrelated example values.
- Show loading, quota/unavailable and retry states. Prevent repeated clicks; recover persisted attempt status by reloading the draft after a lost response.
- In Review order, label the source (`AI suggestion`, `Saved example`, `Manual`) and show unresolved fields and candidate products through the existing checks. Make the initial extraction and approved values inspectable.
- Explain that live extraction sends the pasted text to Gemini before the user starts it. Keep the demo labelled fictional; do not introduce real inbox data in this phase.

Verify: browser checks cover successful extraction, ambiguity resolution, missing address, quantity correction, timeout/retry, lost response, cap exhaustion and no-key fallback. Check desktop and mobile, retained edits, and plain-text rendering of HTML-like email content.

Suggested commit: `feat: add AI draft creation and explicit recovery choices`.

### 6. Verify and document the completed phase

- Extend tests around the existing five sample scenarios; add conflicting instructions, unknown products and prompt-injection-like email text. Assert safe unresolved states as well as correct matches.
- Run frontend lint/build and the complete backend suite. Run database tests against SQLite and disposable PostgreSQL; use existing CI for the PostgreSQL matrix.
- Perform a small, deliberate live smoke check with fictional text only if a verified free-tier key/model is configured. Record model, date and observed results separately from deterministic mocked tests. If unavailable, record live verification as outstanding.
- Update README, `.env.example` and `docs/verification.md` with configuration, limits, failure recovery, provider data handling and known limitations. Document how to disable extraction without losing manual/saved-example access.

Suggested commit: `docs: record AI extraction setup and verification` after checks pass.

## Phase completion gate

All implementation steps and automated/browser checks must pass. A straightforward AI-created order can be reviewed and confirmed; ambiguous or missing data remains blocked until staff resolve it. Original email, validated extraction, normalized initial values and approved values remain inspectable. Failures never silently substitute sample data or overwrite edits. Concurrent requests cannot bypass caps, and extraction cannot change ownership or confirmation rules. Manual and saved-example flows work without Gemini.

Live integration is verified only after the fictional-data smoke check succeeds. Passing mocked tests alone does not establish that the configured provider project works.

## Following phase: public-demo readiness

Before publishing, implement request/body-size enforcement before parsing, guest-creation and API request rate limits, bounded workspace storage/history, and repeatable deletion of expired guests and dependent records. Preserve global usage accounting until its budget window ends even when guest records are deleted, so cleanup cannot reset the cap. Test limits across restarts and guest-session churn. Session caps alone do not prevent visitors from creating new sessions.

Then configure Neon, deploy the built frontend with FastAPI on Render, run migrations and smoke tests, enforce HTTPS cookies, document startup delays, and add the live URL to README. Verify current free-plan limits and a workable cleanup schedule before provisioning; enable no paid upgrades or overages. Recheck all first-release completion criteria before calling the demo public-ready.

## Provider references to check during implementation

- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output): supported schema subset and application-side validation.
- [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing): model-specific free-tier eligibility and data handling. Application caps do not establish the provider account's billing configuration.

Model choice and project quota values are deliberately not frozen in this plan; verify them when enabling live extraction.
