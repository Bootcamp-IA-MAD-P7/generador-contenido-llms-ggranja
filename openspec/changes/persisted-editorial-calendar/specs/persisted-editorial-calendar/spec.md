## ADDED Requirements

### Requirement: persisted editorial calendar
The web client SHALL render persisted editorial plans and MUST not schedule or publish content. Each plan item MAY carry a `scheduled_on` day. The API MUST validate that day within the plan's inclusive `starts_on`–`ends_on` range and persist valid changes.

#### Scenario: Load saved plans
- GIVEN persisted plans exist
- WHEN the calendar view opens
- THEN it shows each item's persisted day or a deterministic in-range fallback day, together with its platform, format, bucket and review-state metadata.

### Requirement: persisted plan-item day changes

The calendar MUST persist a user's selected day through the authenticated plans API. A rejected day change MUST leave the stored plan unchanged.

#### Scenario: move a planned publication within its plan range

- GIVEN a persisted plan item and a chosen day within the plan date range
- WHEN the user moves the item to that day
- THEN `PATCH /plans/{plan_id}/items/{item_index}/day` stores `scheduled_on`
- AND reloading the calendar shows the new day.

#### Scenario: move a planned publication outside its plan range

- GIVEN a persisted plan item
- WHEN the user selects a day before `starts_on` or after `ends_on`
- THEN the API returns 422 and the stored day remains unchanged.

### Requirement: Explicit calendar loading failures
The calendar SHALL expose loading, empty and error states.

#### Scenario: Plans API unavailable
- GIVEN the plans API request fails
- WHEN the calendar view opens
- THEN the user sees an actionable error and no lifecycle state changes.

### Requirement: Validated plan saving
Content Studio SHALL send only validated plan payloads to the plans API.

#### Scenario: Save a plan
- GIVEN a validated editorial plan
- WHEN the user saves it
- THEN it is persisted without generating, approving, scheduling or publishing content.
