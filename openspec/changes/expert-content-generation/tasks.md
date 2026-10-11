# Tasks

## Implementation

- [x] 1. Reconcile the approved image, carousel and Reel content packages with the MVP media-generation boundary in docs/scope.md.
- [x] 2. Confirm Issue #22 as the linked story and update its criteria to reference the approved contract.
- [x] 3. Obtain explicit human approval for the resolved platform/format scope and OpenSpec contract.
- [x] 4. Finalize the guided discovery question map and confirmed/inferred/unknown fact model.
- [x] 5. Finalize goal-to-audience-to-message-to-format-to-CTA decision guidance.
- [x] 6. Curate copy approaches, formulas, persuasion safeguards and visual heuristics from the approved knowledge sources.
- [x] 7. Verify current Meta technical and policy constraints against official documentation.
- [x] 8. Finalize structured input/output schemas in line with the approved application architecture.
- [x] 9. Define the transparent brief-to-post differentiator hypothesis and its validation method.
- [x] 10. Add fixed synthetic or explicitly approved test briefs for the agreed formats and channels.
- [x] 11. Implement the Pydantic `GuidedBrief` model and focused validation tests for required fields, approved platforms/formats and fact statuses.

## Verification

- [x] Verify audience relevance, fact grounding, brand/platform fit, accessibility and editability with representative cases.
- [x] Run OpenSpec schema/active-change validation and the SDD required-field validator.
- [x] Run configured application tests with external provider calls mocked once implementation tasks are approved.
- [x] Record evaluation evidence and limitations against Issue #22.
- [x] Update the daily log and traceability; archive only after implementation, evidence and CI are complete.

## Formula-selection implementation follow-up

- [x] Add the explicit six-formula selector to the review card and pass the selected value to generation/regeneration.
- [x] Return the selected approach, formula and evidence warning in API drafts.
- [x] Verify that formulas requiring confirmed facts warn when the brief has none and never invent proof.
- [x] Run frontend/API tests and validate the OpenSpec change before marking implementation complete.

The Issue #22 contract is approved and its implementation evidence is recorded. Keep the change unarchived until the verification PR is merged and the approved OpenSpec change can be archived.
