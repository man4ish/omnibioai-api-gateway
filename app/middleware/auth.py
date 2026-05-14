from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.iam_client import IAMClient


class AuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, iam: IAMClient):
        super().__init__(app)
        self.iam = iam

    async def dispatch(self, request, call_next):

        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            return JSONResponse({"error": "missing token"}, 401)

        user = await self.iam.validate(token)

        if not user:
            return JSONResponse({"error": "invalid token"}, 401)

        request.state.user = user
        return await call_next(request)