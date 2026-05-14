import httpx


class PolicyClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.http = httpx.AsyncClient(timeout=3)

    async def evaluate(self, payload: dict):
        res = await self.http.post(
            f"{self.base_url}/evaluate",
            json=payload,
        )

        return res.json()