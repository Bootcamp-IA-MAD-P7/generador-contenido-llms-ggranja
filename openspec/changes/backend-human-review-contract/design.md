# Design: Backend human-review transport contract

The existing `EditorialReviewService` remains the sole owner of lifecycle
invariants. FastAPI adapts its result to HTTP and a small in-memory repository
stores records by opaque ID. Chroma remains retrieval-only and is never used as
editorial state storage.

Each generated channel draft is stored separately, with `brand_id` and
`business_id` copied from the request and all existing draft fields retained,
including evidence provenance and supported/unsupported claims. The repository
is process-local and deliberately does not claim restart durability.

`POST /drafts/{content_id}/review` accepts only `approve` or
`request_regeneration`. Both require a declared, unverified `reviewer_ref`;
feedback is required for the regeneration request. `PATCH /drafts/{content_id}`
uses the existing manual-edit service and keeps the item pending. No endpoint
publishes, schedules or exports a non-approved item.

Missing IDs return 404, mismatched or absent recorded regeneration feedback
returns 409, and Pydantic validation errors remain 422. The signed session
dependency protects editorial and plan routes; `/readiness` and `/auth/login`
remain public, while `/auth/me` validates the session and returns its username.
The opaque `content_id` still does not provide tenant authorization: a valid
session is not a per-business access-control decision.

Regeneration accepts the current `GuidedBrief`, the exact feedback already
recorded through the review endpoint, and an optional formula code. The
`EditorialReviewService` validates the lifecycle transition and source feedback,
creates a new content ID and lineage, and leaves the result pending human
review. The selected formula is only a prompt scaffold. Evidence-dependent
formulas remain available when facts are missing but the API rationale and
prompt explicitly prohibit concrete proof or invented results.
