# Design: local demo setup

`scripts/prepare_demo.py` is a local setup helper rather than an application
authentication fallback. It rewrites only named values in ignored `.env` and
`apps/web/.env.local` files, preserving unrelated settings such as model
choices for later provider testing. It writes a PBKDF2 hash for the fixed demo
password and creates a new local signing secret on each invocation. No secret
or password is put into a tracked configuration file.

The setup uses `127.0.0.1:18000`, which keeps browser traffic local and avoids
the previously observed unrelated service on port 8000. The API command still
selects the port explicitly; the web config provides the matching public API
base URL at Next.js startup.

The helper refuses any pre-existing `APP_ENV` other than `development` or an
unset value. It does not alter production code paths, replace authentication,
or enable a cloud provider. Re-running the helper invalidates existing sessions
because it creates a new signing secret; this is acceptable for local demos and
is documented.
