from fastapi import APIRouter, Request
from app.core.proxy import Proxy

router = APIRouter()
proxy = Proxy()


SERVICE_MAP = {
    "tes": "http://tes:8081",
    "toolserver": "http://toolserver:9090",
    "workbench": "http://workbench:8000",
}


@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):

    target = SERVICE_MAP.get(service)

    if not target:
        return {"error": "unknown service"}

    url = f"{target}/{path}"

    body = await request.json() if request.method in ["POST", "PUT"] else None

    status, response = await proxy.forward(
        url=url,
        method=request.method,
        headers=dict(request.headers),
        body=body,
    )

    return {"status": status, "data": response}