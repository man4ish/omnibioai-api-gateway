from fastapi import APIRouter, Request
from app.core.router import resolve_service
from app.core.proxy import ProxyClient
from app.middleware.audit import audit_log

router = APIRouter()
proxy = ProxyClient()


@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):

    target = resolve_service(service)

    if not target:
        return {"error": "unknown service"}

    url = f"{target}/{path}"

    body = None
    try:
        body = await request.json()
    except Exception:
        body = None

    status, response = await proxy.forward(
        url=url,
        method=request.method,
        headers=dict(request.headers),
        body=body,
    )

    await audit_log({
        "event": "gateway_request",
        "service": service,
        "path": path,
        "status": status,
        "user": getattr(request.state, "user", None),
    })

    return {"status": status, "data": response}