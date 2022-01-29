import aiohttp
from discord.ext import commands, tasks
import logging
from requests.structures import CaseInsensitiveDict
import asyncio


class WebUpdate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.base = 'https://aiohttp-MasterBot-web.chawkk6404.repl.co'
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='logs/web.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(handler)
        self.update.start()
        print('Web Dashboard loaded.')

    @property
    def guild_payload(self):
        return {'guild_count': len(self.bot.guilds)}

    @property
    def command_payload(self):
        print([(cmd.name, cmd.cog.qualified_name) for cmd in self.bot.commands])
        return [(cmd.name, cmd.cog.qualified_name) for cmd in self.bot.commands]

    @tasks.loop(minutes=1)
    async def update(self):
        async with self.session.post(self.base + '/guilds', data=self.guild_payload) as resp:
            if resp.status in range(200, 300):
                self.logger.info(f'POST request to /guilds has returned with status {resp.status}')
            else:
                self.logger.info(f'POST request to /guilds has failed with status {resp.status}')
        async with self.session.post(self.base + '/commands', data=self.command_payload) as resp:
            if resp.status in range(200, 300):
                self.logger.info(f'POST request to /commands has returned with status {resp.status}')
            else:
                print(await resp.text())
                self.logger.info(f'POST request to /commands has failed with status {resp.status}')

    @update.before_loop
    async def create_and_wait(self):
        await self.bot.wait_until_ready()
        headers = CaseInsensitiveDict()
        headers['token'] = self.bot.http.token
        self.session = aiohttp.ClientSession(headers=headers)

    @update.after_loop
    async def close_session(self):
        await self.session.close()


def setup(bot):
    bot.add_cog(WebUpdate(bot))
