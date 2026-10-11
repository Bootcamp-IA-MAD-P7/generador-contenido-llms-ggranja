## ADDED Requirements

### Requirement: bounded login attempts

The API SHALL limit repeated login attempts for a client address and normalized
username within a configured sliding window. A blocked request MUST return 429
and MUST NOT reveal whether the username exists.

#### Scenario: login threshold is reached

- GIVEN authentication is configured with a finite attempt threshold
- WHEN the client exceeds that threshold with failed credentials inside the window
- THEN the API returns 429 with retry guidance
- AND it does not issue a session token.

#### Scenario: successful login clears the attempt window

- GIVEN a client has accumulated failed attempts below the threshold
- WHEN valid credentials are submitted
- THEN the API issues a token
- AND the next failed sequence starts with a fresh window for that client and username.

### Requirement: configured multi-user sessions

The API SHALL support an `AUTH_USERS_JSON` mapping of more than one configured
username to password hash while retaining the legacy single-user environment
variables. A valid token MUST identify one configured canonical username.

#### Scenario: second configured user signs in

- GIVEN two configured users with valid password hashes
- WHEN the second user signs in with case-insensitive username input
- THEN the response returns the canonical username
- AND `/auth/me` returns that same username.

### Requirement: owner-scoped editorial resources

New drafts and plans SHALL record the authenticated username as owner. Protected
reads and mutations MUST return 404 when another authenticated user addresses an
owned resource. Legacy ownerless local records MAY remain readable during the
migration period.

#### Scenario: another user cannot access a new draft

- GIVEN one user has created a draft
- WHEN another configured user requests, reviews, regenerates or edits that draft
- THEN the API returns 404 and leaves the draft unchanged.

### Requirement: HTTPS deployment guard

The API SHALL support an opt-in HTTPS requirement for authentication. When the
requirement is enabled, direct HTTPS MUST be accepted, plain HTTP MUST be
rejected, and a trusted proxy MAY establish HTTPS through `X-Forwarded-Proto`.

#### Scenario: hosted authentication refuses plain HTTP

- GIVEN `AUTH_REQUIRE_HTTPS=true` and no trusted HTTPS proxy header
- WHEN a client submits credentials or uses a protected route over HTTP
- THEN the API returns 400 and does not authenticate the request.
