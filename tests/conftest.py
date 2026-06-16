import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Import the app module once — IAMClient/PolicyClient/HPCPolicyClient are
# created as module-level singletons here and injected into the middleware.
# No real connections are made at import time (lazy pools).
import app.main as _main_mod


@pytest.fixture(scope="session")
def client():
    # Stub subscribe_invalidation so the background invalidation task never
    # hits Redis during the test session.
    with patch.object(
        _main_mod.iam,
        "subscribe_invalidation",
        AsyncMock(side_effect=Exception("no redis in tests")),
    ):
        with TestClient(_main_mod.app, raise_server_exceptions=False) as c:
            yield c


@pytest.fixture
def valid_user():
    return {
        "user_id": "123",
        "email": "test@omnibioai.com",
        "roles": ["user"],
        "permissions": ["read:samples"],
    }


@pytest.fixture
def authed(valid_user):
    """Patch iam/policy/hpc so a request is fully authorized."""
    with (
        patch.object(_main_mod.iam, "validate", AsyncMock(return_value=valid_user)),
        patch.object(
            _main_mod.policy,
            "evaluate",
            AsyncMock(return_value={"allowed": True}),
        ),
        patch.object(
            _main_mod.hpc, "evaluate", AsyncMock(return_value={"allow": True})
        ),
    ):
        yield
