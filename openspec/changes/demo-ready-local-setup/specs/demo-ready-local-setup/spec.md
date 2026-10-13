## ADDED Requirements

### Requirement: deterministic local demo preparation

The repository SHALL provide an explicit local-only command that prepares a
deterministic offline demo configuration without requiring a provider key.

#### Scenario: developer prepares a local demo

- GIVEN the project is in an unset or `development` environment
- WHEN the developer runs `python scripts/prepare_demo.py`
- THEN ignored API and web configuration files target `127.0.0.1:18000`
- AND the API uses the `mock` provider
- AND the local login is `gabriela / gabriela`
- AND the repository receives no new secret or credential file.

### Requirement: local demo setup refuses non-development configuration

The local demo helper SHALL refuse to write credentials when an existing
environment is not a development environment.

#### Scenario: production configuration is protected

- GIVEN `.env` declares `APP_ENV=production`
- WHEN the developer runs the local demo helper
- THEN the helper fails before changing `.env` or web configuration.
