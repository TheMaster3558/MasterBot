import requests
import aiohttp


class AsyncHTTPClient:
    def __init__(self, base_url, *, connector: aiohttp.BaseConnector = None, headers=None):
        self.base = base_url
        self._connector = connector
        self.session = aiohttp.ClientSession(connector=self._connector, headers=headers)

    async def create(self):
        if not self.session.closed:
            await self.session.close()
        self.session = aiohttp.ClientSession(connector=self._connector)

    async def request(self, route, **params):
        async with self.session.get(self.base + route, params=params) as resp:
            return await resp.json()


class RequestsHTTPClient:
    def __init__(self, base_url):
        self.base = base_url
        self.session = requests.Session()

    def request(self, route, **params):
        resp = self.session.get(self.base + route, params=params)
        return resp.json()
