"""Tests for app/services/audit_client.py and app/middleware/audit.py audit_log."""
import asyncio
from unittest.mock import AsyncMock, patch


async def test_fire_audit_in_running_loop_creates_task():
    """fire_audit must schedule _emit via create_task when a loop is running."""
    from app.services.audit_client import fire_audit

    with patch("app.services.audit_client._emit", new_callable=AsyncMock) as mock_emit:
        with patch("app.services.audit_client.asyncio.create_task") as mock_create:
            fire_audit({"event": "test"})
            mock_create.assert_called_once()


async def test_fire_audit_exception_silenced():
    """fire_audit must never raise even when asyncio explodes."""
    from app.services.audit_client import fire_audit

    with patch("app.services.audit_client.asyncio.get_event_loop", side_effect=RuntimeError("no loop")):
        fire_audit({"event": "test"})  # must not raise


async def test_audit_log_calls_fire_audit():
    """audit_log (middleware compat wrapper) must delegate to fire_audit."""
    from app.services.audit_client import audit_log, fire_audit

    with patch("app.services.audit_client.fire_audit") as mock_fire:
        await audit_log({"event": "request"})
        mock_fire.assert_called_once_with({"event": "request"})


async def test_middleware_audit_log_calls_fire_audit():
    """app/middleware/audit.py audit_log must call fire_audit."""
    from app.middleware.audit import audit_log

    with patch("app.middleware.audit.fire_audit") as mock_fire:
        await audit_log({"event": "trace_created"})
        mock_fire.assert_called_once_with({"event": "trace_created"})


async def test_emit_calls_redis_xadd():
    """_emit must call xadd on the module-level redis with the event payload."""
    import json
    from app.services import audit_client

    mock_redis = AsyncMock()
    original = audit_client._redis
    audit_client._redis = mock_redis
    try:
        await audit_client._emit({"event": "e1", "data": 42})
        mock_redis.xadd.assert_called_once()
        args, kwargs = mock_redis.xadd.call_args
        assert args[0] == "audit:events"
        payload = json.loads(args[1]["data"])
        assert payload["event"] == "e1"
    finally:
        audit_client._redis = original


async def test_emit_xadd_error_silenced():
    """_emit must swallow redis errors."""
    from app.services import audit_client

    mock_redis = AsyncMock()
    mock_redis.xadd.side_effect = RuntimeError("redis down")
    original = audit_client._redis
    audit_client._redis = mock_redis
    try:
        await audit_client._emit({"event": "e1"})  # must not raise
    finally:
        audit_client._redis = original
