# Design

Add a narrow plans API client in the web domain. Calendar renders persisted plan items grouped by plan and uses each plan range as its date context. Content Studio only invokes the existing save endpoint for an already validated EditorialPlan payload; plan construction rules remain in the backend domain. A failed fetch or save stays visible and cannot change review or publication state.

Each `PlannedItem` carries an optional `scheduled_on` date so existing stored
plans remain readable. A new authenticated `PATCH /plans/{plan_id}/items/{item_index}/day`
operation returns and persists an updated plan. The planning domain validates
the item index and requires the date to fall inclusively between `starts_on` and
`ends_on`; the storage layer continues to store the validated plan as one JSON
payload. Calendar moves update the UI only after the API confirms the save.
Items without `scheduled_on` receive a deterministic display fallback clamped
to the plan range. Synthetic sample items remain session-only.
