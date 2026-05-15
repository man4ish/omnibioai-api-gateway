import os


class Config:
    IAM_URL = os.getenv("IAM_URL", "http://omnibioai-auth:8000")
    POLICY_URL = os.getenv("POLICY_URL", "http://omnibioai-policy-engine:8001")
    HPC_URL = os.getenv("HPC_URL", "http://omnibioai-hpc-policy-engine:8002")
    AUDIT_REDIS = os.getenv("AUDIT_REDIS", "redis://redis:6379")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
    SERVICE_SECRET = os.getenv("GATEWAY_SECRET", "dev-secret")
    ROUTE_TIMEOUT = int(os.getenv("ROUTE_TIMEOUT", "15"))
