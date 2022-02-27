import slash_util
import discord
from discord.ext import commands
from time import perf_counter
from typing import Optional, Iterable
import os
from prefix import Prefix, get_prefix
import traceback
import sys
import logging


intents = discord.Intents.default()
intents.members = True


class MasterBot(slash_util.Bot):
    __version__ = '1.1.1'

    def __init__(self, cr_api_key, weather_api_key, mongo_db):
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

    async def on_ready(self):
        print('Logged in as {0} ID: {0.id}'.format(self.user))
        self.on_ready_time = perf_counter()
        print('Time taken to ready up:', round(self.on_ready_time - self.start_time, 1), 'seconds')

    async def on_command_error(self, context: commands.Context, exception: commands.errors.CommandError) -> None:
        if not context.command:
            return
        if not hasattr(context.command.cog, 'on_command_error') and not context.command.has_error_handler():
            traceback.print_exception(exception, file=sys.stderr)

    def run(self, token) -> None:
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
        super().run(token)

    def restart(self):
        """Reloads all extensions and clears the cache"""
        extensions = list(self.extensions).copy()
        for ext in extensions:
            self.reload_extension(ext)
        self.clear()

    @property
    def oath_url(self):
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
                        scopes: Optional[Iterable[str]] = None):
        if not self.user:
            return
        return discord.utils.oauth_url(self.user.id,
                                       permissions=permissions,
                                       scopes=scopes)
