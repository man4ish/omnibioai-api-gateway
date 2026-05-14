import uuid
from app.middleware.audit import audit_log


def generate_trace_id() -> str:
    return str(uuid.uuid4())


async def attach_trace(request):
    trace_id = generate_trace_id()
    request.state.trace_id = trace_id

    await audit_log({
        "event": "trace_created",
        "trace_id": trace_id,
        "path": request.url.path,
        "method": request.method,
    })

    return trace_id