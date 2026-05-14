from fastapi import FastAPI

from app.middleware.auth import AuthMiddleware
from app.middleware.policy import PolicyMiddleware
from app.middleware.s2s import S2SMiddleware

from app.services.iam_client import IAMClient
from app.services.policy_client import PolicyClient
from app.core.config import Config

from app.routes.gateway import router

app = FastAPI(title="OmniBioAI API Gateway")

iam = IAMClient(Config.IAM_URL)
policy = PolicyClient(Config.POLICY_URL)

app.add_middleware(AuthMiddleware, iam=iam)
app.add_middleware(PolicyMiddleware, policy=policy)
app.add_middleware(S2SMiddleware)

app.include_router(router)