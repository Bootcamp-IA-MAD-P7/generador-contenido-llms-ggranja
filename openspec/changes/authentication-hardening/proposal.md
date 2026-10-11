# Proposal

## Status and human approval

- Status: Approved
- Issue: #115 — Harden prototype authentication for team deployment
- Human approval: explicit implementation request in the project conversation on 2026-10-11.

## Plan objective

Make the prototype authentication boundary safe enough for a controlled team
deployment while preserving the simple local development path.

## Objective

Limit repeated login attempts, support multiple configured users, bind newly
created editorial resources to the authenticated user and make HTTPS a required
deployment setting when the API is exposed outside localhost.

## Scope

### Included

- A process-local sliding-window login-attempt limiter.
- `AUTH_USERS_JSON` as an opt-in multi-user credential configuration with the
  existing single-user variables retained for compatibility.
- Ownership checks for newly created drafts and editorial plans.
- `AUTH_REQUIRE_HTTPS` and an opt-in trusted-proxy check for
  `X-Forwarded-Proto`.
- Focused auth, ownership, environment and API tests plus deployment guidance.

### Excluded

- Certificate issuance, TLS termination or a hosting-provider choice.
- OAuth, password reset, account administration and shared rate-limit storage.
- Automatic migration of legacy local records that have no owner.

## Acceptance criteria

- Repeated failed logins receive 429 after the configured threshold and a
  successful login clears the attempt window for that client and username.
- More than one configured user can authenticate and receives a token for the
  canonical configured username.
- New drafts and plans are readable and mutable only by their owner; legacy
  ownerless local records remain compatible and are documented.
- When HTTPS is required, plain HTTP authentication requests fail, direct HTTPS
  succeeds and a trusted proxy may supply the HTTPS scheme.
- Local HTTP defaults remain usable and no secret is added to the repository.

## Rubric

No aplica — this is a focused security hardening change for a controlled
prototype deployment, not a new product capability or model-quality rubric.

## Tests and verification

- Automated: focused FastAPI tests with synthetic credentials and no provider calls.
- Contract: OpenSpec, SDD and full project test validation.
- Manual/evidence: inspect environment guidance and protected resource behavior.

## Open questions and blockers

- The process-local limiter is intentionally not shared across multiple API
  workers; a hosted deployment must add shared rate-limit storage if it scales
  beyond one process.
- TLS termination and certificate management remain deployment concerns outside
  this repository.
- Legacy ownerless local records are readable during migration and are not
  automatically reassigned.

## Approval

Approved by the user's explicit instruction to proceed with authentication
hardening after the MVP verification work was merged.
