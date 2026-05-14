import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import Config


class S2SMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        token = request.headers.get("X-Service-Token")

        if not token:
            return JSONResponse({"error": "missing service token"}, 401)

        try:
            payload = jwt.decode(token, Config.SERVICE_SECRET, algorithms=["HS256"])
        except Exception:
            return JSONResponse({"error": "invalid service token"}, 401)

        request.state.service = payload.get("service")

        return await call_next(request)