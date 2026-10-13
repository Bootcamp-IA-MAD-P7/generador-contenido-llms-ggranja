# Design: authentication hardening

`apps/api/auth.py` remains a standard-library boundary. `AuthSettings` parses
the legacy single-user variables and, when present, an `AUTH_USERS_JSON` object
whose keys are canonical usernames and whose values are PBKDF2 hashes. Token
subjects are canonical configured usernames; `require_session` rejects tokens
for users that are no longer configured.

Login attempts use a process-local, lock-protected sliding window keyed by the
client address and case-folded username. The default is five attempts per five
minutes. The limiter is deliberately bounded to one process; a real deployment
must add an edge or gateway rate limit when more than one API instance runs.

`AUTH_REQUIRE_HTTPS` is false for local development and true for a hosted
deployment. Direct HTTPS is accepted. `AUTH_TRUST_PROXY=true` additionally
allows the first value of `X-Forwarded-Proto` to establish HTTPS, under the
deployment's responsibility to overwrite that header at the trusted proxy.
Authentication endpoints fail with 400 when the required secure transport is
absent; readiness remains available for local diagnostics.

`EditorialContent.owner_username` and `EditorialPlan.owner_username` are
optional for backwards-compatible local payloads. API-created records always
set the current session username, and owner-aware reads, reviews, regeneration,
edits and plan-day mutations return 404 for another user's owned record. Older
ownerless records remain readable so an existing local prototype is not broken;
they must be migrated or recreated before a hosted multi-user rollout.
