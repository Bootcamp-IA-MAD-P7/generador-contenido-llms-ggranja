# Proposal

## Status and human approval

- Status: Approved
- Issue: #35 — Create demo scenarios, test data and fallback plan
- Human approval: the user explicitly requested a stable local demo login and
  an MVP ready for testing/demo on 2026-10-13.

## Plan objective

Make the offline MVP demo reproducible on a developer machine without relying
on a conflicting default port, external LLM credentials or manually copied
random local passwords.

## Scope

### Included

- An idempotent local-only helper that configures `gabriela / gabriela`, the
  deterministic mock provider and loopback port 18000 in ignored files.
- Frontend API configuration for the same local port.
- Documentation and focused tests for setup behavior and production refusal.

### Excluded

- A production/default password, hosted deployment configuration or a bypass of
  authentication.
- Groq/Ollama execution, social publication or new product behavior.

## Acceptance criteria

- `python scripts/prepare_demo.py` creates ignored local config for API and web
  and exposes a reproducible local login as `gabriela / gabriela`.
- The helper forces the deterministic `mock` provider and API port 18000.
- The helper refuses an existing non-development `APP_ENV`.
- No plaintext password, signing secret or provider credential is committed.
- The local demo guide includes start, login and verification steps.

## Rubric

- C1.2: supports a reproducible functional demo and fallback preparation.
- C4: supports offline MVP validation but does not claim a real-model run.

## Tests and evidence

- Focused Python tests verify generated config, hash validation, web URL,
  credential file and production refusal.
- Existing API, web tests and typecheck remain the regression check.

## Open questions and blockers

- The helper chooses 18000 to avoid the observed local collision on 8000; it
  cannot guarantee any arbitrary computer has that port free.
- Real Groq and Ollama smoke tests remain a separate credential/service task.
