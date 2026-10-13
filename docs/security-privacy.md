# Security and Privacy Boundaries

Authority: canonical security and privacy baseline.
Bootstrap issue: #37.

- Never commit API keys, OAuth tokens, environment files or personal access tokens.
- Persist OAuth tokens only through an approved encrypted server-side mechanism.
- Request only permissions needed for the selected Instagram action.
- Use synthetic or explicitly approved business data in provider free-tier evaluation.
- Treat generated content as a draft until human review.
- Do not publish to Instagram without explicit confirmation for that post.
- Log decisions and test evidence without exposing client secrets or unapproved business information.
- External API tests MUST use mocks by default; real smoke tests require an authorized test account.
- Any privacy or permission change requires a new Issue and approved OpenSpec contract.

## Authentication hardening

The API keeps the original single-user environment variables for local work and
also accepts `AUTH_USERS_JSON`, a JSON object mapping usernames to PBKDF2 password
hashes, when more than one team member needs access. New drafts and plans record
the authenticated username; another configured user cannot retrieve or mutate
those owned records. Legacy local records without an owner remain readable for
backwards compatibility and must be migrated or recreated before a hosted
multi-user rollout.

Login attempts are limited per client address and normalized username through
`AUTH_LOGIN_MAX_ATTEMPTS` within `AUTH_LOGIN_WINDOW_SECONDS`. The limiter is
process-local, so a hosted deployment with multiple API instances still needs a
shared edge or gateway rate limit.

Set `AUTH_REQUIRE_HTTPS=true` in a hosted deployment. If TLS terminates at a
trusted reverse proxy, set `AUTH_TRUST_PROXY=true` so the API may honor an
`X-Forwarded-Proto: https` value that the proxy sets. The local default remains
HTTP for development; the API does not issue certificates or terminate TLS.
