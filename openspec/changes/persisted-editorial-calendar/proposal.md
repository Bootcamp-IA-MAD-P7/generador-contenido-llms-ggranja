# Proposal

## Status and human approval

- Status: Approved
- Issue: #106 — Connect editorial calendar to persisted plans and Content Studio
- Human approval: initial contract approved on 2026-10-10; persistence of user-moved days approved in the project conversation on 2026-10-11.

## Plan objective

Finish the visible MVP workflow by displaying persisted editorial plans and saving user-selected days in the existing calendar view.

## Objective

Replace the calendar placeholder with a plan view backed by FastAPI and let Content Studio save only already validated plans. Persist a day for each planned item and validate it within the plan's date range.

## Scope

Included: web API client for the plans API, loading/error/empty states, dated plan-item calendar rendering, saving a validated plan, and persisting a user's day changes for each plan item. Each scheduled day is validated within the plan date range and stored with its item.

Excluded: external calendar sync, new allocation rules, automatic content creation, new review states and social-platform scheduling or publication. Calendar drag/drop only changes the planned day in the local editorial plan.

## Acceptance criteria

- The calendar loads persisted plans and shows dates, platform, format, bucket and review-state source metadata.
- Empty/error states are explicit.
- Content Studio can save an existing validated plan without generating or approving content.
- Each publication has an optional persisted `scheduled_on` day; changing it updates the stored plan and survives reload.
- The API rejects a day outside the plan's inclusive `starts_on`–`ends_on` range and does not alter the stored plan.
- No calendar action schedules or publishes.
- Existing frontend, Python, SDD, OpenSpec and diff checks pass.

## Rubric

No aplica — integration of existing MVP planning/persistence capabilities.

## Tests and verification

Use synthetic persisted plans and mocked fetch. No provider, publishing or external-calendar calls.

## Open questions and blockers

Visual density remains limited to the current MVP data model.

## Approval

Approved. The user explicitly extended this contract on 2026-10-11 to persist moved days inside each plan's date range.
