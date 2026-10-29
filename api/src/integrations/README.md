Gemini extraction uses the official `google-genai` SDK. `schemas.py` bounds provider facts,
`matching.py` makes deterministic catalogue suggestions, `gemini.py` makes one bounded
structured-output call, and `usage.py` serializes durable database reservations.

Prompts treat email as untrusted data. No tools, prices, stock, approvals, catalogue IDs or
confirmation decisions are delegated to the model. Relative dates have no trusted source
clock; absolute dates require an explicit year and an excerpt present in the original email.

Live extraction defaults off and requires an explicit key and model. Verify the actual
project's free-tier eligibility, structured-output support and quotas before enabling it.
See the [README](../../../README.md#configuration) for setup and data handling,
and [operations](../../../docs/operations.md) for public limits and cleanup. Tests require no
provider credentials or network. GitHub OAuth and Resend remain second-release work.
