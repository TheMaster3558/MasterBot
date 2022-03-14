import requests
import aiohttp


def cleanup_params(params: dict) -> dict:
    return {k: v for k, v in params.items() if v is not None}


class AsyncHTTPClient:
    def __init__(self, base_url, *, connector: aiohttp.BaseConnector = None, headers=None, loop=None,
                 session: aiohttp.ClientSession = None):
        self.base = base_url
        self._connector = connector
        self.loop = loop
        self.headers = headers
        self.session = session

    async def create(self):
        if self.session:
            if not self.session.closed:
                await self.session.close()
        self.session = aiohttp.ClientSession(connector=self._connector, headers=self.headers, loop=self.loop)

    async def request(self, route, json=True, **params):
        params = cleanup_params(params)
        async with self.session.get(self.base + route, params=params) as resp:
            if json:
                return await resp.json()
            return await resp.text()

    def __del__(self):
        self.loop.create_task(self.session.close())


class RequestsHTTPClient:
    def __init__(self, base_url):
        self.base = base_url
        self.session = requests.Session()

    def request(self, route, json=True, **params):
        resp = self.session.get(self.base + route, params=params)
        if json:
            return resp.json()
        return resp.text

    def __del__(self):
        self.session.close()
