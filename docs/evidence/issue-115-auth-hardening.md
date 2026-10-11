# Issue #115 — Authentication hardening evidence

Status: implementation prepared on `feat/115-auth-hardening`; implementation
PR toward `dev` is opened after the local verification below.

## Scope verified

- Login attempts are bounded per client address and normalized username, with a
  `429` response and `Retry-After` guidance.
- `AUTH_USERS_JSON` supports multiple configured identities while preserving
  the legacy single-user environment variables.
- New drafts and plans store the canonical authenticated username and reject
  cross-user reads and mutations with `404`.
- `AUTH_REQUIRE_HTTPS` rejects plain HTTP authentication; direct HTTPS and an
  explicitly trusted `X-Forwarded-Proto: https` proxy path are accepted.
- Local defaults remain compatible with HTTP development and no credential or
  secret was added to the repository.

## Automated verification

Run from the repository root:

```text
python -m pytest -q
152 passed, 55 subtests passed in 0.61s

python -m pytest -q tests/test_auth.py tests/test_auth_ownership.py
10 passed

npm test -- --runInBand        (apps/web)
37 passed

npm run typecheck              (apps/web)
passed

python scripts/validate_sdd_contract.py
SDD contract validation passed.

npm exec --yes --package=@fission-ai/openspec@1.13.2 -- openspec schema validate sdd-governance
Schema 'sdd-governance' is valid

npm exec --yes --package=@fission-ai/openspec@1.13.2 -- openspec validate --all --json
20 passed, 0 failed

git diff --check
passed
```

The web build is not part of this evidence: the local runner has the known
`uv_resident_set_memory` `ENOENT` failure during `next build`, unrelated to
this change.

## Deployment limitations

The limiter is process-local. A multi-worker or multi-instance deployment
must add an edge or shared rate limit. TLS termination and certificate
management remain outside the API. Legacy ownerless local records remain
readable for compatibility and should be migrated or recreated before a
hosted multi-user rollout.
