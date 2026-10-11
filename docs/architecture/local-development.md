# Local development contract

This document describes the runnable foundation currently delivered by Issue #21.
It intentionally does not describe provider-backed generation or social publishing.

## Prerequisites

- Python 3.11 or newer;
- Node.js 22 and npm;
- Git.

The API uses FastAPI, Pydantic, Uvicorn and LangChain Core. The web client uses
Next.js, React and TypeScript. The supported application test command is
`python -m pytest -q` from the repository root.

## Clean local setup

From a checkout of the repository:

```text
python -m venv .venv
```

Activate the virtual environment, then install the Python dependencies:

```text
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create the local environment file from the safe template:

```text
copy .env.example .env
```

`.env` is local-only and ignored by Git. The foundation defaults need no provider
credentials. Do not add API keys or tokens to `.env.example`, the browser bundle,
or the repository.

Editorial drafts and plans persist locally by default at `.local/editorial.sqlite3`.
Set `EDITORIAL_DATABASE_PATH` in `.env` only when a different local file is needed.

To use the real Groq text provider locally, set these values in `.env` after
creating a development key in the Groq console. Keep `LLM_PROVIDER=mock` when
running offline tests:

```text
LLM_PROVIDER=groq
GROQ_API_KEY=<local-only-secret>
GROQ_MODEL=openai/gpt-oss-20b
LLM_TEMPERATURE=0.2
LLM_TIMEOUT_SECONDS=30
```

To use an already installed local Ollama model, configure the API host and model explicitly. The API sends no credentials and does not download models or fall back to a cloud provider:

```text
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=<installed-local-model>
LLM_TEMPERATURE=0.2
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=350
```

## Run the foundation

Use two terminals from the repository root.

Terminal 1 — API:

```text
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

The API exposes `/readiness`, `/docs`, `/redoc` and `/openapi.json`.
With `LLM_PROVIDER=groq` or `LLM_PROVIDER=ollama`, `POST /drafts` uses the selected API-side adapter and returns editable drafts for human review. The browser never receives provider credentials.

Authentication is configured locally with `AUTH_USERNAME`,
`AUTH_PASSWORD_HASH` and `AUTH_SECRET`. For a team deployment, replace the
single-user pair with `AUTH_USERS_JSON`, a JSON object whose values are PBKDF2
hashes compatible with `apps.api.auth.hash_password` (generate them with the
local helper or a deployment secret manager); each newly created draft or
plan is owned by the signed-in username. Login attempts are bounded by
`AUTH_LOGIN_MAX_ATTEMPTS` and `AUTH_LOGIN_WINDOW_SECONDS`.

Hosted deployments must set `AUTH_REQUIRE_HTTPS=true`. When a trusted reverse
proxy terminates TLS, set `AUTH_TRUST_PROXY=true` and configure that proxy to
overwrite `X-Forwarded-Proto`; never trust a client-supplied forwarding header
when the API is directly reachable. Local development keeps these flags false.

To ingest the official Coll Amunt! PDF into the ignored local RAG store, place
the downloaded source at `.local/rag/sources/2025-Coll-Amunt-Llibre-_compressed.pdf`
and run `python scripts/ingest_collamunt.py`. The command preserves Catalan
page text, source provenance, a SHA-256 digest and stable business identifiers;
re-running it uses the same chunk IDs and Chroma upsert semantics. Enable the
grounded API path with `rag_enabled=true`, `business_id` and optional `top_k` in
`POST /drafts`.

Terminal 2 — web client:

```text
npm --prefix apps/web ci
npm --prefix apps/web run dev
```

Open `http://localhost:3000`. The client reads `NEXT_PUBLIC_API_BASE_URL`, which
defaults to `http://127.0.0.1:8000` when it is not set.

## Tests and build

```text
python -m pytest -q
python scripts/validate_sdd_contract.py
npm --prefix apps/web run build
```

The SDD harness installs `requirements.txt`, validates OpenSpec governance, and
uses `python -m pytest -q` as its configured application-test command.

## Repository structure

- `apps/api/`: FastAPI app, environment settings and the provider-neutral LangChain boundary;
- `apps/web/`: Next.js client and the readiness connection;
- `tests/`: governance, API, environment and boundary tests;
- `docs/architecture/`: system and local-development documentation;
- `openspec/changes/web-foundation/`: approved contract and task evidence;
- `.env.example`: safe, non-secret local configuration template.

## Current foundation boundary

The foundation provides local API readiness, OpenAPI documentation, safe
environment defaults, the LangChain Core boundary and a deterministic offline
mock adapter. Baseline tests use synthetic data and make no external provider
calls.

The following are not part of this phase: Groq or Gemini calls, RAG, content
generation, model comparison, OAuth, Instagram/Facebook publishing, images,
voice, LinkedIn, production hosting, multi-tenant behavior and Docker adoption.
