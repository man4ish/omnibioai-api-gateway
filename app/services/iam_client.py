import json
from typing import Callable, Optional

import httpx
import redis.asyncio as aioredis


class IAMClient:
    def __init__(self, base_url: str, redis_url: str):
        self.base_url = base_url.rstrip("/")
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.http = httpx.AsyncClient(timeout=3)

    # ------------------------------------------------------------------
    # Cache helpers  (key: iam:{token}, TTL 5 min)
    # ------------------------------------------------------------------
    async def _get_cached(self, token: str) -> Optional[dict]:
        try:
            raw = await self.redis.get(f"iam:{token}")
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def _set_cached(self, token: str, user: dict, ttl: int = 300):
        try:
            await self.redis.setex(f"iam:{token}", ttl, json.dumps(user))
        except Exception:
            pass

    async def evict(self, token: str):
        try:
            await self.redis.delete(f"iam:{token}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Validate token: cache-first, then remote auth service (1 retry)
    # ------------------------------------------------------------------
    async def validate(self, token: str) -> Optional[dict]:
        cached = await self._get_cached(token)
        if cached:
            return cached

        for attempt in range(2):
            try:
                res = await self.http.post(
                    f"{self.base_url}/auth/validate",
                    json={"token": token},
                    timeout=3,
                )
                data = res.json()

                if not data.get("valid"):
                    await self.evict(token)
                    return None

                user = {
                    "user_id": str(data["user_id"]),
                    "email": data.get("email", ""),
                    "roles": data.get("roles", []),
                    "permissions": data.get("permissions", []),
                    "valid": True,
                }
                await self._set_cached(token, user)
                return user

            except httpx.TimeoutException:
                if attempt == 0:
                    continue
                return None
            except Exception:
                return None

        return None

    # ------------------------------------------------------------------
    # Redis Pub/Sub — subscribe to "policy:invalidate" channel
    # on_invalidate(user_id, token) is called for each message
    # ------------------------------------------------------------------
    async def subscribe_invalidation(self, on_invalidate: Callable):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("policy:invalidate")
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await on_invalidate(
                        data.get("user_id", ""),
                        data.get("token", ""),
                    )
                except Exception:
                    pass
