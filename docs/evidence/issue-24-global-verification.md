# Issue #24 — global verification evidence

This record verifies the merged #24.1, #24.2 and #24.3 implementation together,
including the session-protected regeneration route and reviewer-selected formula
scaffold added in the final review iteration.

## Acceptance criteria

| Criterion | Evidence | Result |
| --- | --- | --- |
| Human review is explicit | `EditorialContent` separates `generated_draft`, `pending_human_review` and `approved_final`; `approve` requires a non-empty reviewer reference. | Pass |
| Regeneration accepts feedback or changed inputs | `RegenerationRequest` validates the two triggers; `regenerate` records source draft ID, source fingerprint, feedback/changed inputs and preserves evidence, assumptions, review notes, provenance and unsupported-claim metadata. | Pass |
| Session-protected formula regeneration | `POST /drafts/{content_id}/regenerate` requires `require_session`, matches the exact recorded feedback, accepts the current brief and optional formula, and returns a new pending-review item with lineage. | Pass |
| Evidence warning for selected formulas | PAS, BAB and 4 Ps return a visible rationale warning when the brief has no confirmed facts; the prompt treats the formula as structure and does not add proof. | Pass |
| Copy/export is limited to final approved text | `copy_final` and `export_final` require `approved_final` and return only the exact caption with content ID, channel and format metadata. | Pass |

## Required safeguards

- `manual_edit` keeps content in `pending_human_review` and clears the prior approval/feedback record; editing cannot approve implicitly.
- Invalid state transitions raise `EditorialTransitionError`.
- Regeneration returns a new pending-review item with lineage and preserved GuidedBrief/RAG-related draft metadata; provider failures preserve the source item.
- Regeneration rejects feedback that differs from the feedback recorded by the reviewer and rejects unknown formula codes.
- Missing session credentials reject regeneration and plan mutations; `/readiness` remains public.
- Generated and pending-review content cannot be copied or exported as final; the source state remains unchanged.
- Tests use synthetic content and do not publish, call a real LLM provider, write to a CMS or export media/files.

## Executed validation

- `npm exec --yes --package=@fission-ai/openspec@1.13.2 -- openspec schema validate sdd-governance`: passed.
- `npm exec --yes --package=@fission-ai/openspec@1.13.2 -- openspec validate --all --json`: 19/19 items passed, 0 failed. The existing informational archive warning for `required-ci-efficiency` is unrelated to this change.
- `python scripts/validate_sdd_contract.py`: passed.
- `python -m pytest -q`: 148 passed, 55 subtests passed.
- `python -m pytest tests/test_regenerate_api.py tests/test_api_calendar.py tests/test_auth.py -q`: 13 passed.
- `npm test` in `apps/web`: 37 passed.
- `npm run typecheck` in `apps/web`: passed.
- `npm run build` in `apps/web`: blocked by the local runner's `ENOENT: uv_resident_set_memory`; this is unrelated to the documentation change.
- `git diff --check`: passed.
- GitHub Actions SDD Harness for PR #113, run `38117195939`: passed, including OpenSpec schema, active-change, required-field and configured application tests.

## Limitations

The evidence is deterministic unit/smoke coverage over synthetic fixtures. It does not claim external-provider availability, production clipboard integration, CMS export, publication, or rubric completion beyond the Issue #24 acceptance criteria. Issue #24 is closed; the OpenSpec change remains active until its approved implementation is archived after the verification PR is merged.
