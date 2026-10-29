> Historical plan: Original project plan. Status statements describe the planning baseline, not the current release. See the [README](../../README.md) for current behavior and setup.

**Repository:** `email-to-order`

A web application that turns customer emails into checked, editable order drafts. Staff review the details, resolve issues and confirm each order.

**Purpose:** reduce the time distributors spend interpreting emails and manually retyping orders.

## 1. Core workflow

1. Load a sample email or paste email text.
2. AI extracts the requested order details.
3. Backend checks the draft against customer and product records.
4. Staff review the original email beside the editable order.
5. Staff resolve missing or ambiguous information.
6. **Confirm order** saves the final order and generates an order number.
7. Show a simulated confirmation email.

The app uses one fictional distributor, seeded customers, products, addresses and stock.

## 2. First-release scope

Include:

- Sample emails and pasted email text.
- AI extraction into structured drafts.
- Customer selection and saved delivery addresses.
- Product matching using SKUs, names and aliases.
- Quantity, pack-size and simulated stock checks.
- Catalogue prices and calculated line totals in one currency.
- Editable drafts with clear warnings and blocking issues.
- Confirmation, order history and a confirmation preview.
- Temporary guest workspaces, isolated between visitors.

Preserve the original email, initial extraction and final approved values so staff corrections are inspectable.

## 3. Order rules

AI suggests values. Backend code validates them.

An order can be confirmed only when:

- A customer is selected.
- Every line matches a catalogue product.
- Quantities are positive and units or pack sizes are clear.
- A delivery address is confirmed.
- Simulated stock is sufficient.
- All blocking issues are resolved.

Missing information stays empty. Uncertain matches require staff review. Saved addresses may be suggested but must not silently replace conflicting email instructions.

Prices come from the catalogue. Requested delivery dates do not represent guaranteed delivery.

Confirmation rechecks the draft and prevents duplicate orders. Confirmed orders are read-only in the first release.

## 4. Simple UI flow

|Screen|Content|Main action|
|---|---|---|
|**Orders**|Draft and confirmed orders|New order|
|**New order**|Sample selection or pasted email|Create draft|
|**Review order**|Original email, editable draft and flagged issues|Confirm order|
|**Confirmed order**|Order number, final details and confirmation preview|Back to orders|

```
Try demo
  → Choose sample or paste email
  → Create draft
  → Review and correct
  → Confirm order
  → View confirmed order
```

Show clear loading, failure and retry states. If live AI extraction is unavailable, offer a clearly labelled saved example.

## 5. Tech stack

|Part|Technology|
|---|---|
|Frontend|React, TypeScript, Vite|
|Interface|Tailwind CSS, shadcn/ui|
|Backend|Python, FastAPI|
|Validation|Pydantic|
|Database|PostgreSQL on Neon|
|Database access|SQLAlchemy|
|Migrations|Alembic|
|AI|Gemini API using an eligible free-tier model|
|Testing|pytest and frontend build checks|
|Automation|GitHub Actions|
|Hosting|Render Free|

Use a monorepo:

```
email-to-order/
├── app/                    # React frontend
├── api/
│   ├── src/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── auth/
│   │   ├── orders/
│   │   ├── customers/
│   │   ├── catalogue/
│   │   └── integrations/
│   ├── migrations/
│   ├── tests/
│   └── pyproject.toml
├── .github/workflows/
├── .env.example
└── README.md
```

Feature folders use `router.py`, `service.py`, `schemas.py` and `models.py` where needed.

During development, React forwards API requests to FastAPI. When deployed, FastAPI serves the built React files and API under one public origin.

## 6. Security and public access

Visitors can try the demo without an account.

- Issue a guest session and isolate each visitor’s orders.
- Check access permissions on the backend.
- Keep database credentials and API keys on the backend.
- Limit request sizes, AI usage and requests per visitor.
- Set a global daily extraction cap.
- Display incoming email content as plain text.
- Treat email text and AI output as untrusted input.
- Expire guest sessions and clean up temporary records.
- Use fictional data and clearly label simulated behaviour.

## 7. Second release: login and real email

Once the core workflow works:

- Add GitHub OAuth using Authlib and backend-managed sessions.
- Give signed-in users saved workspaces.
- Connect a Resend receiving address to a verified backend webhook.
- Fetch incoming email content and create drafts.
- Restrict the connected inbox and real sending to the owner.
- Add **Confirm & Send** for real confirmation delivery.
- Track delivery separately so failed emails can be retried without duplicating orders.

Public visitors continue to use fictional examples and confirmation previews.

## 8. $0 deployment target

- **Render Free:** host FastAPI and the built frontend.
- **Neon Free:** host PostgreSQL.
- **Gemini free tier:** perform limited live extraction.
- **Included hosting URL:** avoid buying a domain.
- **Version one:** no email provider required.
- **Later:** use Resend within its free allowances and test-sending restrictions.

Free hosting has usage limits and cold starts. The demo should explain startup delays and remain useful when AI quotas are exhausted. Do not enable paid upgrades or overages.

## 9. Build plan

1. **Seed data:** products, customers, addresses and sample emails.
2. **Manual workflow:** draft editing, checks and confirmation.
3. **AI extraction:** structured output, ambiguity handling and retries.
4. **Public access:** guest isolation, usage limits and cleanup.
5. **Verification:** test matching, quantities, addresses, ownership and duplicate confirmation.
6. **Deployment:** publish the demo and document setup.
7. **Integrations:** add GitHub login and real email.

## 10. Completion criteria

A visitor can:

- Confirm a straightforward order.
- Resolve an ambiguous product.
- Supply a missing delivery address.
- Correct a quantity or pack-size issue.
- Recover from extraction failure.
- Retry confirmation without creating a duplicate.
- Access only their own workspace.

The README includes the live link, screenshots, architecture, setup instructions and known limitations. Any time-saving claim uses the same sample orders for manual entry and assisted review, including correction time.

**Outside the initial scope:** attachments, OCR, payments, tax and shipping calculations, inventory reservations, backorders, vector search, customer portals and real distributor-system integrations.
