from app.middleware.audit import audit_log


class AuditClient:
    async def emit(self, event: dict):
        await audit_log(event)