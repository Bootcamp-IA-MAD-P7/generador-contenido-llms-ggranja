# Tasks

## Contract and configuration

- [x] Create Issue #115 and approve the authentication-hardening scope.
- [x] Preserve legacy single-user variables and document multi-user/HTTPS settings.

## Implementation

- [x] Add bounded process-local login-attempt limiting with retry guidance.
- [x] Add `AUTH_USERS_JSON` parsing and canonical multi-user sessions.
- [x] Store the authenticated owner on new drafts and plans.
- [x] Enforce owner-aware reads and mutations for editorial resources.
- [x] Add the opt-in HTTPS and trusted-proxy transport guard.

## Verification

- [x] Add focused tests for rate limiting, multiple users, ownership and HTTPS.
- [x] Run Python, web, SDD, OpenSpec and diff validation.
- [ ] Record CI evidence and open the implementation PR toward `dev`.
