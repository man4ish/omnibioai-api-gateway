import os


class Config:
    IAM_URL = os.getenv("IAM_URL", "http://omnibioai-auth:8000")
    POLICY_URL = os.getenv("POLICY_URL", "http://policy-engine:8001")
    AUDIT_URL = os.getenv("AUDIT_URL", "redis://redis:6379")

    SECRET = os.getenv("GATEWAY_SECRET", "dev-secret")