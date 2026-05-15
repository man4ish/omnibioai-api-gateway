from typing import Optional

import httpx


class PolicyClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.http = httpx.AsyncClient(timeout=3)

    async def evaluate(
        self,
        user: dict,
        path: str,
        method: str,
        trace_id: str = "",
    ) -> dict:
        payload = {
            "user_id": user.get("user_id", ""),
            "email": user.get("email", ""),
            "roles": user.get("roles", []),
            "permissions": user.get("permissions", []),
            "action": f"{method.lower()}.{path.strip('/').replace('/', '.')}",
            "resource": path,
            "context": {"method": method, "path": path},
        }
        headers = {
            "X-Internal-Service": "gateway",
            "X-Trace-Id": trace_id,
            "X-User-Id": user.get("user_id", ""),
        }

        for attempt in range(2):
            try:
                res = await self.http.post(
                    f"{self.base_url}/policy/evaluate",
                    json=payload,
                    headers=headers,
                    timeout=3,
                )
                return res.json()
            except httpx.TimeoutException:
                if attempt == 0:
                    continue
                return {"allowed": False, "reason": "policy_timeout"}
            except Exception:
                return {"allowed": False, "reason": "policy_error"}

        return {"allowed": False, "reason": "policy_unavailable"}
