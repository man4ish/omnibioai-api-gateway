import asyncio
import json

import redis.asyncio as aioredis

from app.core.config import Config

_redis = aioredis.from_url(Config.AUDIT_REDIS, decode_responses=True)
STREAM = "audit:events"


async def _emit(event: dict):
    try:
        await _redis.xadd(
            STREAM,
            {"data": json.dumps(event, default=str)},
            maxlen=1_000_000,
            approximate=True,
        )
    except Exception:
        pass


def fire_audit(event: dict):
    """Schedule a non-blocking audit write. Never raises."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_emit(event))
    except Exception:
        pass


async def audit_log(event: dict):
    """Async fire-and-forget wrapper kept for import compatibility."""
    fire_audit(event)
