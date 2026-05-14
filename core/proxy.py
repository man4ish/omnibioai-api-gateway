import httpx


class Proxy:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10)

    async def forward(self, url: str, method: str, headers=None, body=None):
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            json=body,
        )
        return response.status_code, response.json()