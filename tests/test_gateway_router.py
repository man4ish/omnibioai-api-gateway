"""
Tests for the gateway catch-all route (app/routes/gateway.py).

Route pattern: /{service}/{path:path}
resolve_service() maps service slug → upstream URL.
Unknown service → {"error": "unknown service"} with HTTP 200.
Known service → proxy attempt (upstream unreachable in tests → HTTP 200 with
                upstream_failure body, not a 4xx from the gateway itself).
"""
from unittest.mock import AsyncMock, patch

import app.main as _main_mod
from app.core.router import SERVICE_MAP


def test_unknown_service_returns_error_body(client, valid_user):
    with (
        patch.object(_main_mod.iam, "validate", AsyncMock(return_value=valid_user)),
        patch.object(
            _main_mod.policy,
            "evaluate",
            AsyncMock(return_value={"allowed": True}),
        ),
    ):
        resp = client.get(
            "/nonexistent-service/some/path",
            headers={"Authorization": "Bearer token"},
        )
    assert resp.status_code == 200
    assert resp.json().get("error") == "unknown service"


def test_known_service_does_not_return_unknown_error(client, valid_user):
    """A known service must be forwarded — the gateway error body must not appear."""
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
            "/workbench/ping", headers={"Authorization": "Bearer token"}
        )
    assert resp.json().get("error") != "unknown service"


def test_service_map_contains_expected_services():
    for svc in ("workbench", "tes", "toolserver", "model-registry", "rag"):
        assert svc in SERVICE_MAP, f"{svc} missing from SERVICE_MAP"
