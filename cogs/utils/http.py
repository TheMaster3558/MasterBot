import asyncio

import requests
import aiohttp


def cleanup_params(params: dict) -> dict:
    return {k: v for k, v in params.items() if v is not None}


class AsyncHTTPClient:
    session: aiohttp.ClientSession | None = None

    def __init__(
            self,
            base_url,
            *,
            headers=None,
            loop=None,
            suffix: str = ""
    ):
        self.base = base_url
        self.loop = loop
        self.headers = headers
        self.suffix = suffix

    @classmethod
    async def create(cls, loop: asyncio.AbstractEventLoop = None):
        if cls.session is not None:
            return
        cls.session = aiohttp.ClientSession(loop=loop)

    async def request(self, route, json=True, method: str = 'GET', **params):
        params = cleanup_params(params)
        async with self.session.request(method,
                                        self.base + route + self.suffix, params=params, headers=self.headers
                                        ) as resp:
            if json:
                return await resp.json()
            return await resp.text()

    @classmethod
    async def close(cls):
        if not cls.session:
            return
        if not cls.session.closed:
            await cls.session.close()
