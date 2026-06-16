"""
Tests for PolicyMiddleware (app/middleware/policy.py).

PolicyClient.evaluate() returns {"allowed": bool, "reason": str}.
The middleware returns 403 {"error": "forbidden", "reason": ...} on denial.
"""
from unittest.mock import AsyncMock, patch

import app.main as _main_mod


def test_policy_denial_returns_403(client, valid_user):
    with (
        patch.object(_main_mod.iam, "validate", AsyncMock(return_value=valid_user)),
        patch.object(
            _main_mod.policy,
            "evaluate",
            AsyncMock(return_value={"allowed": False, "reason": "no_permission"}),
        ),
    ):
        resp = client.get(
            "/workbench/", headers={"Authorization": "Bearer token"}
        )
    assert resp.status_code == 403
    data = resp.json()
    assert data.get("error") == "forbidden"
    assert data.get("reason") == "no_permission"


def test_policy_approval_passes_through(client, valid_user):
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
        resp = client.get(
            "/workbench/", headers={"Authorization": "Bearer token"}
        )
    assert resp.status_code != 403


def test_policy_denial_without_reason(client, valid_user):
    """reason key absent — middleware should default gracefully."""
    with (
        patch.object(_main_mod.iam, "validate", AsyncMock(return_value=valid_user)),
        patch.object(
            _main_mod.policy,
            "evaluate",
            AsyncMock(return_value={"allowed": False}),
        ),
    ):
        resp = client.get(
            "/workbench/", headers={"Authorization": "Bearer token"}
        )
    assert resp.status_code == 403
    assert resp.json().get("error") == "forbidden"


def test_policy_middleware_no_user_returns_403():
    """PolicyMiddleware must return 403 when request.state.user is absent."""
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient
    from app.middleware.policy import PolicyMiddleware

    async def dummy(request):
        return PlainTextResponse("ok")

    inner_app = Starlette(routes=[Route("/secure", dummy)])
    inner_app.add_middleware(PolicyMiddleware, policy=AsyncMock())

    with TestClient(inner_app, raise_server_exceptions=False) as c:
        resp = c.get("/secure")

    assert resp.status_code == 403
    assert resp.json()["error"] == "forbidden"
