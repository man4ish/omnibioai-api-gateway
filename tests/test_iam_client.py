"""Tests for app/services/iam_client.py — IAMClient unit tests."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.iam_client import IAMClient


@pytest.fixture
def iam_client():
    # Use MagicMock so pubsub() returns a plain mock (not a coroutine).
    # Async methods are explicitly overridden with AsyncMock.
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock()
    mock_redis.setex = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_http = AsyncMock()
    with (
        patch("app.services.iam_client.aioredis.from_url", return_value=mock_redis),
        patch("app.services.iam_client.httpx.AsyncClient", return_value=mock_http),
    ):
        client = IAMClient("http://iam-service", "redis://localhost")
    return client, mock_redis, mock_http


async def test_get_cached_hit(iam_client):
    client, mock_redis, _ = iam_client
    user = {"user_id": "42", "valid": True}
    mock_redis.get.return_value = json.dumps(user)
    result = await client._get_cached("tok")
    assert result == user
    mock_redis.get.assert_called_once_with("iam:tok")


async def test_get_cached_miss_returns_none(iam_client):
    client, mock_redis, _ = iam_client
    mock_redis.get.return_value = None
    assert await client._get_cached("tok") is None


async def test_get_cached_redis_error_returns_none(iam_client):
    client, mock_redis, _ = iam_client
    mock_redis.get.side_effect = ConnectionError("redis down")
    assert await client._get_cached("tok") is None


async def test_set_cached_calls_setex(iam_client):
    client, mock_redis, _ = iam_client
    user = {"user_id": "1"}
    await client._set_cached("tok", user, ttl=60)
    mock_redis.setex.assert_called_once_with("iam:tok", 60, json.dumps(user))


async def test_set_cached_default_ttl(iam_client):
    client, mock_redis, _ = iam_client
    await client._set_cached("tok", {"user_id": "1"})
    args = mock_redis.setex.call_args[0]
    assert args[1] == 300


async def test_set_cached_redis_error_silenced(iam_client):
    client, mock_redis, _ = iam_client
    mock_redis.setex.side_effect = RuntimeError("redis down")
    await client._set_cached("tok", {"user_id": "1"})  # must not raise


async def test_evict_calls_delete(iam_client):
    client, mock_redis, _ = iam_client
    await client.evict("tok")
    mock_redis.delete.assert_called_once_with("iam:tok")


async def test_evict_redis_error_silenced(iam_client):
    client, mock_redis, _ = iam_client
    mock_redis.delete.side_effect = RuntimeError("redis down")
    await client.evict("tok")  # must not raise


async def test_validate_cache_hit_returns_cached(iam_client):
    client, mock_redis, mock_http = iam_client
    user = {"user_id": "7", "valid": True}
    mock_redis.get.return_value = json.dumps(user)
    result = await client.validate("tok")
    assert result == user
    mock_http.post.assert_not_called()


async def test_validate_remote_valid_returns_user(iam_client):
    client, mock_redis, mock_http = iam_client
    mock_redis.get.return_value = None
    resp = MagicMock()
    resp.json.return_value = {
        "valid": True,
        "user_id": "99",
        "email": "u@test.com",
        "roles": ["admin"],
        "permissions": ["write"],
    }
    mock_http.post.return_value = resp
    result = await client.validate("tok")
    assert result is not None
    assert result["user_id"] == "99"
    assert result["email"] == "u@test.com"
    assert result["roles"] == ["admin"]
    assert result["valid"] is True


async def test_validate_remote_invalid_evicts_and_returns_none(iam_client):
    client, mock_redis, mock_http = iam_client
    mock_redis.get.return_value = None
    resp = MagicMock()
    resp.json.return_value = {"valid": False}
    mock_http.post.return_value = resp
    result = await client.validate("tok")
    assert result is None
    mock_redis.delete.assert_called_once_with("iam:tok")


async def test_validate_timeout_first_attempt_retries_and_succeeds(iam_client):
    client, mock_redis, mock_http = iam_client
    mock_redis.get.return_value = None
    resp = MagicMock()
    resp.json.return_value = {
        "valid": True,
        "user_id": "55",
        "email": "",
        "roles": [],
        "permissions": [],
    }
    mock_http.post.side_effect = [httpx.TimeoutException("t/o"), resp]
    result = await client.validate("tok")
    assert result is not None
    assert result["user_id"] == "55"


async def test_validate_timeout_both_attempts_returns_none(iam_client):
    client, mock_redis, mock_http = iam_client
    mock_redis.get.return_value = None
    mock_http.post.side_effect = httpx.TimeoutException("t/o")
    assert await client.validate("tok") is None


async def test_validate_generic_exception_returns_none(iam_client):
    client, mock_redis, mock_http = iam_client
    mock_redis.get.return_value = None
    mock_http.post.side_effect = RuntimeError("network error")
    assert await client.validate("tok") is None


async def test_subscribe_invalidation_calls_callback_on_message(iam_client):
    client, mock_redis, _ = iam_client
    received = []

    async def on_invalidate(user_id, token):
        received.append((user_id, token))

    messages = [
        {"type": "subscribe", "data": 1},
        {"type": "message", "data": json.dumps({"user_id": "u1", "token": "t1"})},
        {"type": "message", "data": json.dumps({"user_id": "u2", "token": "t2"})},
    ]

    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()

    async def listen_gen():
        for msg in messages:
            yield msg

    mock_pubsub.listen = listen_gen
    mock_redis.pubsub.return_value = mock_pubsub

    await client.subscribe_invalidation(on_invalidate)

    assert received == [("u1", "t1"), ("u2", "t2")]


async def test_subscribe_invalidation_bad_json_silenced(iam_client):
    client, mock_redis, _ = iam_client
    called = []

    async def on_invalidate(user_id, token):
        called.append(True)

    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()

    async def listen_gen():
        yield {"type": "message", "data": "not-json"}

    mock_pubsub.listen = listen_gen
    mock_redis.pubsub.return_value = mock_pubsub

    await client.subscribe_invalidation(on_invalidate)

    assert called == []


async def test_subscribe_invalidation_callback_exception_silenced(iam_client):
    client, mock_redis, _ = iam_client

    async def on_invalidate(user_id, token):
        raise RuntimeError("callback error")

    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()

    async def listen_gen():
        yield {"type": "message", "data": json.dumps({"user_id": "u", "token": "t"})}

    mock_pubsub.listen = listen_gen
    mock_redis.pubsub.return_value = mock_pubsub

    await client.subscribe_invalidation(on_invalidate)  # must not raise


async def test_subscribe_invalidation_missing_fields_defaults(iam_client):
    client, mock_redis, _ = iam_client
    received = []

    async def on_invalidate(user_id, token):
        received.append((user_id, token))

    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()

    async def listen_gen():
        yield {"type": "message", "data": json.dumps({})}

    mock_pubsub.listen = listen_gen
    mock_redis.pubsub.return_value = mock_pubsub

    await client.subscribe_invalidation(on_invalidate)

    assert received == [("", "")]
