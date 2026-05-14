from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.policy_client import PolicyClient


class PolicyMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, policy: PolicyClient):
        super().__init__(app)
        self.policy = policy

    async def dispatch(self, request, call_next):

        decision = await self.policy.evaluate({
            "user": getattr(request.state, "user", None),
            "path": request.url.path,
            "method": request.method,
        })

        if not decision.get("allow"):
            return JSONResponse(
                {"error": "forbidden", "reason": decision.get("reason")},
                status_code=403
            )

        return await call_next(request)