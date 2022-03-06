from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from time import perf_counter
from typing import Optional, Iterable, TypeVar
from prefix import Prefix, get_prefix
import traceback
import sys
import logging
import asyncio
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=UserWarning, module='fuzzywuzzy')
    from fuzzywuzzy import fuzz


MasterBotT = TypeVar('MasterBotT', bound='MasterBot')
CogT = TypeVar('CogT', bound=commands.Cog)


class MasterBot(commands.Bot):
    __version__ = '1.3.0'

    def __init__(self, cr_api_key: str, weather_api_key: str, mongo_db: str, /) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(command_prefix=get_prefix,
                         intents=intents,
                         help_command=None,
                         activity=discord.Game(f'version {self.__version__}'),
                         strip_after_prefix=True,
                         enable_debug_events=True)
        self.add_cog(Prefix(self))

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

        self.tree = app_commands.CommandTree(self)

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

    async def on_ready(self) -> None:
        print('Logged in as {0} ID: {0.id}'.format(self.user))
        self.on_ready_time = perf_counter()
        print('Time taken to ready up:', round(self.on_ready_time - self.start_time, 1), 'seconds')
        await self.tree.sync(guild=discord.Object(id=878431847162466354))

    async def on_command_error(self, context: commands.Context, exception: commands.errors.CommandError) -> None:
        if not context.command:
            return
        if isinstance(exception, commands.CommandNotFound):
            possibles = [cmd for cmd in self.all_commands if fuzz.ratio(
                    context.message.content,
                    cmd
                ) > 70
            ]
            if len(possibles) > 0:
                embed = discord.Embed(title="I couldn't find that command",
                                      description='Maybe you meant\n{}'.format(
                                          "\n".join(possibles)
                                      ))
                await context.reply(embed=embed, mention_author=False)
        if not context.cog.has_error_handler() and not context.command.has_error_handler():
            traceback.print_exception(exception, file=sys.stderr)

    def run(self, token: str) -> None:
        cogs = [
            'cogs.clash_royale',
            'cogs.code',
            'cogs.help_info',
            'cogs.jokes',
            'cogs.moderation',
            'cogs.reaction_roles',
            'cogs.translate',
            'cogs.trivia',
            'cogs.weather',
            'cogs.webhook',
            'cogs.forms',
            'cogs.math',
            'cogs.games'
        ]
        for cog in cogs:
            self.load_extension(cog)
        for name, cog in self.cogs.items():
            if name == 'Prefix':
                continue
            self.tree.add_command(cog, override=True)  # type: ignore
        super().run(token)

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
