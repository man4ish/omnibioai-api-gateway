import os


class Config:
    IAM_URL = os.getenv("IAM_URL", "http://omnibioai-auth:8000")
    POLICY_URL = os.getenv("POLICY_URL", "http://omnibioai-policy-engine:8001")
    AUDIT_REDIS = os.getenv("AUDIT_REDIS", "redis://redis:6379")

    SERVICE_SECRET = os.getenv("GATEWAY_SECRET", "dev-secret")

    ROUTE_TIMEOUT = int(os.getenv("ROUTE_TIMEOUT", "15"))