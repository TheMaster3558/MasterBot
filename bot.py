import slash_util
import discord
from discord.ext import commands
from time import perf_counter
from typing import Literal, Optional

intents = discord.Intents.default()
intents.members = True


class MasterBot(slash_util.Bot):
    __version__ = '1.0.0a'
    # two tokens for my two bots
    TOKEN1 = 'OTI0MDM1ODc4ODk1MTEyMjUz.YcYteQ.JFJ5PrKgDX8lvQE-p5bQWKGFBBs'
    TOKEN2 = 'ODc4MDM1MDY3OTc5NTYzMDY5.YR7T4Q.oD3Gk9-jNwpYOje5Iz9C8ZN-Xhc'

    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('!'),
                         intents=intents,
                         help_command=None,
                         activity=discord.Game(f'version {self.__version__}'),
                         strip_after_prefix=True)
        self.start_time = perf_counter()
        self.on_ready_time = None
        self.current_token: Optional[Literal[1, 2]] = None

    async def on_ready(self):
        print('Logged in as {0} ID: {0.id}'.format(self.user))
        self.on_ready_time = perf_counter()
        print('Time taken to ready up:', round(self.on_ready_time - self.start_time, 1), 'seconds')

    def run(self, token: Optional[Literal[1, 2]] = 1) -> None:
        cogs = [
            'cogs.reaction_roles',
            'cogs.moderation',
            'cogs.code',
            'cogs.translate',
            'cogs.trivia',
            'cogs.help_info',
            'cogs.clash_royale',
            'cogs.jokes',
            'cogs.webhook'
        ]
        for cog in cogs:
            self.load_extension(cog)
        if token == 1:
            self.current_token = self.TOKEN1
        elif token == 2:
            self.current_token = self.TOKEN2
        super().run(self.current_token)
