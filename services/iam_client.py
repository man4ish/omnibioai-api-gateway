import httpx


class IAMClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.http = httpx.AsyncClient(timeout=3)

    async def validate(self, token: str):
        res = await self.http.post(
            f"{self.base_url}/auth/validate",
            json={"token": token},
        )

        if res.status_code != 200:
            return None

        data = res.json()
        return data if data.get("valid") else None