import json
import redis.asyncio as redis
from app.core.config import Config


_redis = redis.from_url(Config.AUDIT_REDIS, decode_responses=True)
STREAM = "audit:gateway"


async def audit_log(event: dict):
    await _redis.xadd(
        STREAM,
        {"data": json.dumps(event)},
        maxlen=1_000_000,
        approximate=True,
    )