"""
Tests for HPCMiddleware (app/middleware/hpc.py).

HPC_COMPUTE_SERVICES = {"tes", "toolserver", "workbench"}.
The middleware is only applied to these services.
HPCPolicyClient.evaluate() returns {"allow": bool, "reason": str}.
Denial → 403 {"error": "HPC quota exceeded", "reason": ...}.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.main as _main_mod
from app.services.hpc_policy_client import HPC_COMPUTE_SERVICES


def test_hpc_denial_returns_403(client, valid_user):
    with (
        patch.object(_main_mod.iam, "validate", AsyncMock(return_value=valid_user)),
        patch.object(
            _main_mod.policy,
            "evaluate",
            AsyncMock(return_value={"allowed": True}),
        ),
        patch.object(
            _main_mod.hpc,
            "evaluate",
            AsyncMock(return_value={"allow": False, "reason": "quota_exceeded"}),
        ),
    ):
        resp = client.get("/workbench/", headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403
    data = resp.json()
    assert data.get("error") == "HPC quota exceeded"
    assert data.get("reason") == "quota_exceeded"


def test_hpc_approval_passes_through(client, valid_user):
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
        resp = client.get("/workbench/", headers={"Authorization": "Bearer token"})
    assert resp.status_code != 403


def test_hpc_not_called_for_non_compute_service(client, valid_user):
    """model-registry is not in HPC_COMPUTE_SERVICES — hpc.evaluate must not fire."""
    assert "model-registry" not in HPC_COMPUTE_SERVICES
    mock_hpc_eval = AsyncMock()
    with (
        patch.object(_main_mod.iam, "validate", AsyncMock(return_value=valid_user)),
        patch.object(
            _main_mod.policy,
            "evaluate",
            AsyncMock(return_value={"allowed": True}),
        ),
        patch.object(_main_mod.hpc, "evaluate", mock_hpc_eval),
    ):
        client.get("/model-registry/v1", headers={"Authorization": "Bearer token"})
    mock_hpc_eval.assert_not_called()


@pytest.mark.parametrize("service", sorted(HPC_COMPUTE_SERVICES))
def test_is_compute_service_true_for_known_services(service):
    assert _main_mod.hpc.is_compute_service(service) is True


def test_is_compute_service_false_for_unknown():
    assert _main_mod.hpc.is_compute_service("unknown-service") is False
