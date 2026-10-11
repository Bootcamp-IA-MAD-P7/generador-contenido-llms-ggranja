# Backend human-review contract

## ADDED Requirements

### Requirement: authenticated session and protected API

The API MUST expose `POST /auth/login` to exchange configured credentials for
an expiring bearer token and `GET /auth/me` to return the authenticated
username. Draft, review, regeneration, edit and plan operations MUST require a
valid session.

#### Scenario: signed-in reviewer identity is available

- GIVEN a valid session token
- WHEN the client requests `GET /auth/me`
- THEN the response includes the username associated with the session.

#### Scenario: protected operation has no valid session

- GIVEN no valid bearer token
- WHEN the caller requests a draft, review, regeneration, edit or plan operation
- THEN the API returns 401 and does not mutate editorial state.

### Requirement: feedback-driven regeneration endpoint

`POST /drafts/{content_id}/regenerate` MUST require a valid session, a current
brief and feedback that exactly matches the feedback recorded for that source
draft. It MAY accept one explicitly selected formula. The API MUST create a
new content ID, preserve source lineage and business/RAG provenance, and return
the new draft to `pending_human_review` without approving it.

#### Scenario: recorded feedback regenerates a draft

- GIVEN a pending draft with a recorded `request_regeneration` review
- AND the request feedback exactly matches the stored feedback
- WHEN the client posts a brief and optional formula to the regeneration endpoint
- THEN the API creates a new pending-review draft linked to the source draft
- AND retains the feedback, evidence provenance and selected formula rationale.

#### Scenario: feedback is missing or differs from the recorded value

- GIVEN the source draft has no matching recorded feedback decision
- WHEN regeneration is requested
- THEN the API returns 409 and does not create a new draft.

#### Scenario: evidence-dependent formula has no confirmed facts

- GIVEN the selected formula relies on proof or a real before/after situation
- AND the brief has no confirmed facts
- WHEN the draft is regenerated
- THEN the response warns that the brief lacks confirmed facts
- AND the prompt prohibits invented evidence, outcomes and proof.

### Requirement: reviewable draft identity and retrieval

The API MUST assign each generated channel draft a stable `content_id` and
MUST preserve its brand, business, editorial, provenance and grounding fields.

#### Scenario: generated draft is retrievable

- GIVEN POST `/drafts` returns a non-empty draft
- WHEN the caller requests GET `/drafts/{content_id}`
- THEN the same draft is returned with `pending_human_review`
- AND its business and source metadata are unchanged.

### Requirement: explicit review decisions

The API MUST require a non-empty declared reviewer reference for approval or a
feedback decision, and SHALL reject invalid lifecycle transitions.

#### Scenario: approval is explicit

- GIVEN a draft is pending human review
- WHEN a reviewer submits `approve` with a reviewer reference
- THEN the item becomes `approved_final`
- AND a second approval is rejected.

#### Scenario: manual edit is not approval

- GIVEN a draft is pending human review
- WHEN the caller edits its caption
- THEN the item remains `pending_human_review`.

### Requirement: safe scope and persistence boundary

The API MUST return 404 for an unknown content ID and MUST NOT use Chroma as
editorial state storage. The process-local implementation MUST document that
records are not durable across a service restart.

#### Scenario: unknown content is isolated

- GIVEN a content ID from another business or an unknown ID
- WHEN the caller retrieves it
- THEN no other business content is returned
- AND the response is an actionable 404.
