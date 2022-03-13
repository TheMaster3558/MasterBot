"""
MasterBot
~~~~~~~~~~
a Discord Bot with many uses and more to come

:copyright: (c) 2021-present The Master
:license: Mozilla Public License Version 2.0, see LICENSE for more
"""


from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils.cog import Cog
from time import perf_counter
from typing import Optional, Iterable, TypeVar
import logging
import asyncio
import traceback
import sys
import re
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=UserWarning, module='fuzzywuzzy')
    from fuzzywuzzy import fuzz


MasterBotT = TypeVar('MasterBotT', bound='MasterBot')
CogT = TypeVar('CogT', bound=Cog)


class MasterBot(commands.Bot):
    __version__ = '1.4.2'
    test_guild = discord.Object(id=878431847162466354)

    def __init__(self, cr_api_key: str, weather_api_key: str, mongo_db: str, /) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or('!'),
                         intents=intents,
                         help_command=None,
                         activity=discord.Game(f'version {self.__version__}'),
                         strip_after_prefix=True,
                         enable_debug_events=True)

        self.start_time = perf_counter()
        self.on_ready_time = None

        self.clash_royale = cr_api_key
        self.weather = weather_api_key

        self.prefixes = {}
        self.prefixes_db = None
        self.moderation_mongo = mongo_db

        logger = logging.getLogger('discord')
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)

        self.locks: dict[CogT, asyncio.Lock] = {}

        self.regexes: dict[str, re.Pattern] = {
            'bot token': re.compile(r'[A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}'),
            'email': re.compile(r'[\w\d]+\.\w+\.[a-z]{2,4}'),
            'phone number': re.compile(r'\(?\d{3}\)?-?\d{3}-?\d{4}')
        }

    async def on_message(self, message: discord.Message):

        await self.process_commands(message)

    def acquire_lock(self, cog: CogT) -> asyncio.Lock:
        if cog not in self.locks:
            self.locks[cog] = asyncio.Lock()
        return self.locks[cog]

    @classmethod
    def custom(cls, cr_api_key: str, weather_api_key: str, mongo_db: str, /,
               command_prefix='!', **options) -> MasterBotT:
        self = cls(cr_api_key, weather_api_key, mongo_db)
        self.command_prefix = command_prefix
        for k, v in options:
            setattr(self, k, v)
        return self

    async def delete_app_commands(self):
        await self.http.bulk_upsert_global_commands(self.application_id, payload=[])

    def load_extensions(self):
        cogs = [
            'cogs.clash_royale',
            'cogs.help_info',
            'cogs.code',
            'cogs.forms',
            'cogs.games',
            'cogs.math',
            'cogs.moderation',
            'cogs.reaction_roles',
            'cogs.translate',
            'cogs.trivia',
            'cogs.webhook',
            'cogs.weather',
            'cogs.jokes',
            'cogs.version'
        ]
        for cog in cogs:
            self.load_extension(cog)

    async def setup_hook(self) -> None:
        self.load_extensions()

    async def on_ready(self):
        self.on_ready_time = perf_counter()
        print('Logged in as {0} ID: {0.id}'.format(self.user))
        print('Time taken to start up:', round(self.on_ready_time - self.start_time, 1), 'seconds')
        await self.tree.sync()

    async def on_command_error(self, context: commands.Context, exception: commands.errors.CommandError) -> None:
        if isinstance(exception, commands.CommandNotFound):
            possibles = [cmd for cmd in self.all_commands if fuzz.ratio(
                    context.message.content,
                    cmd
                ) > 70
            ]
            if len(possibles) > 0:
                embed = discord.Embed(title="I couldn't find that command",
                                      description='Maybe you meant:\n`{}`'.format("`\n`".join(possibles)))
                await context.reply(embed=embed, mention_author=False)
            return
        if not context.cog.has_error_handler() and context.command.has_error_handler():
            traceback.print_exception(exception, file=sys.stderr)

    def restart(self):
        """Reloads all extensions and clears the cache"""
        extensions = list(self.extensions).copy()
        for ext in extensions:
            self.reload_extension(ext)
        self.clear()

    @property
    def oath_url(self) -> Optional[str]:
        if not self.user:
            return
        permissions = discord.Permissions(manage_roles=True,
                                          manage_channels=True,
                                          kick_members=True,
                                          ban_members=True,
                                          manage_webhooks=True,
                                          moderate_members=True,
                                          send_messages=True,
                                          add_reactions=True)
        scopes = ('bot', 'applications.commands')
        return discord.utils.oauth_url(self.user.id,
                                       permissions=permissions,
                                       scopes=scopes)

    def custom_oath_url(self, permissions: Optional[discord.Permissions] = None,
                        scopes: Optional[Iterable[str]] = None) -> Optional[str]:
        if not self.user:
            return
        return discord.utils.oauth_url(self.user.id,
                                       permissions=permissions,
                                       scopes=scopes)
