import pytest

from apps.api.auth import require_session
from apps.api.main import app


@pytest.fixture(autouse=True)
def signed_in_session():
    """Existing API tests exercise editorial behaviour, not sign-in: provide a session.

    Authentication itself is covered in ``test_auth.py``, which removes this override.
    """

    app.dependency_overrides[require_session] = lambda: "test-user"
    yield
    app.dependency_overrides.pop(require_session, None)
