import requests
import aiohttp


def cleanup_params(params: dict) -> dict:
    return {k: v for k, v in params.items() if v is not None}


class AsyncHTTPClient:
    def __init__(
        self,
        base_url,
        *,
        connector: aiohttp.BaseConnector = None,
        headers=None,
        loop=None,
        session: aiohttp.ClientSession = None,
        suffix: str = ""
    ):
        self.base = base_url
        self.connector = connector
        self.loop = loop
        self.headers = headers
        self.session = session
        self.suffix = suffix

    async def create(self):
        if self.session:
            if not self.session.closed:
                await self.session.close()
        self.session = aiohttp.ClientSession(
            connector=self.connector, headers=self.headers, loop=self.loop
        )

    async def request(self, route, json=True, **params):
        params = cleanup_params(params)
        async with self.session.get(
            self.base + route + self.suffix, params=params
        ) as resp:
            if json:
                return await resp.json()
            return await resp.text()

    async def close(self):
        if not self.session:
            return
        if not self.session.closed:
            await self.session.close()
