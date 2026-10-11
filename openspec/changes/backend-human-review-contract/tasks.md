# Tasks

## Implementation

- [x] 1. Add process-local editorial storage separate from Chroma.
- [x] 2. Preserve brand, business, grounding and provenance metadata in content records.
- [x] 3. Expose draft retrieval, review status, explicit review decisions and manual edits.
- [x] 4. Return safe HTTP errors and require a declared reviewer for decisions.
- [x] 5. Add an authenticated feedback-driven regeneration endpoint that requires an exact match with the recorded feedback, accepts the current brief and optional formula, and preserves lineage/evidence.
- [x] 6. Protect the regeneration route with the signed session dependency and verify unauthenticated access is rejected.
- [x] 7. Update the API contract for `/auth/login`, `/auth/me`, and the new regeneration request/response fields.

## Verification

- [x] 8. Add focused API tests for creation, retrieval, lifecycle transitions, isolation and metadata preservation.
- [ ] 9. Test regeneration feedback matching, formula selection, missing-evidence warnings and session protection.
- [ ] 10. Run focused tests, SDD/OpenSpec validation and `git diff --check`.

All tasks are complete for the approved 20.5.1 scope. Durable persistence and
identity verification remain outside this iteration.
