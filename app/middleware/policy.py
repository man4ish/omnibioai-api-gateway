from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.policy_client import PolicyClient
from app.services.audit_client import fire_audit

_SKIP_PATHS = {"/health", "/"}


class PolicyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, policy: PolicyClient):
        super().__init__(app)
        self.policy = policy

    async def dispatch(self, request, call_next):
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        user = getattr(request.state, "user", None)
        trace_id = getattr(request.state, "trace_id", "")

        if not user:
            return JSONResponse({"error": "forbidden"}, status_code=403)

        decision = await self.policy.evaluate(
            user=user,
            path=request.url.path,
            method=request.method,
            trace_id=trace_id,
        )

        if not decision.get("allowed", False):
            fire_audit({
                "service": "gateway",
                "event_type": "policy_denied",
                "user_id": user.get("user_id"),
                "action": f"{request.method} {request.url.path}",
                "decision": "deny",
                "reason": decision.get("reason", "policy_block"),
                "trace_id": trace_id,
            })
            return JSONResponse(
                {"error": "forbidden", "reason": decision.get("reason")},
                status_code=403,
            )

        return await call_next(request)
