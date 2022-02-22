import slash_util
from bot import MasterBot
from cogs.utils.http import AsyncHTTPClient


class AsyncGoogleHTTPClient(AsyncHTTPClient):
    def __init__(self, loop):
        super().__init__('https://google.com/search', loop=loop)


class Google(slash_util.Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = AsyncHTTPClient(self.bot.loop)


def setup(bot: MasterBot):
    bot.add_cog(Google(bot))
