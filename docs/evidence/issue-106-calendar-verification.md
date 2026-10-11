# Issue #106 — persisted calendar verification evidence

This record verifies the persisted editorial-calendar slice merged in PR #113.
It covers the selected day stored on each planned item, the inclusive plan-range
guard, the authenticated update route and the frontend persistence client.

## Acceptance criteria

| Criterion | Evidence | Result |
| --- | --- | --- |
| Planned items can carry a day | `PlannedItem.scheduled_on` is optional, survives JSON storage and is returned by the plans API. | Pass |
| Valid moves persist | `PATCH /plans/{plan_id}/items/{item_index}/day` calls `reschedule_item`, stores the validated plan and a subsequent GET returns the selected day. | Pass |
| Invalid moves are rejected safely | Dates before `starts_on` or after `ends_on` return 422; an invalid item index returns 404; the stored item remains unchanged after rejection. | Pass |
| Calendar UI uses the persistence API | `updatePlanItemDay` sends the selected ISO date and the calendar only updates its visible item after the API confirms the save. | Pass |
| Calendar mutations require a session | The day-update route uses `require_session`; unauthenticated plan mutations return 401. | Pass |

## Executable evidence

- `tests/test_api_calendar.py` covers valid persistence, reload, out-of-range
  rejection, missing items and unchanged storage.
- `tests/test_editorial_planning.py` covers the date-range invariant and the
  pure rescheduling operation.
- `apps/web/tests/review-api.test.ts` covers the frontend PATCH request and
  returned `scheduled_on` value.
- `apps/web/tests/calendar-layout.test.ts` covers month rendering and the
  local movement calculation used by the calendar.
- Local verification: `python -m pytest tests/test_api_calendar.py -q` passes;
  the complete Python suite passes with 148 tests and 55 subtests, and the web
  suite passes with 37 tests.
- OpenSpec schema validation passes and `openspec validate --all --json`
  reports 19/19 items valid.
- GitHub Actions SDD Harness for PR #113, run `38117195939`, passed the
  configured application tests and OpenSpec validation.

## Boundaries

The calendar changes an editorial plan day only. They do not schedule or publish
to a social platform, sync an external calendar or bypass human review.
