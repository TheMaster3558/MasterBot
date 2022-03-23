from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands
from cogs.utils.help_utils import HelpSingleton
import re
from typing import ClassVar, TYPE_CHECKING

if TYPE_CHECKING:
    from bot import MasterBot


class CogMeta(type(commands.Cog)):
    def __new__(cls, *args, **kwargs):
        help_command = kwargs.pop('help_command', None)
        new_cls = super().__new__(cls, *args, **kwargs)  # type: ignore
        new_cls.help_command = help_command
        return new_cls


class Cog(commands.Cog, metaclass=CogMeta):
    help_command: ClassVar[HelpSingleton]

    def __init__(self, bot: MasterBot):
        self.bot = bot

    async def cog_load(self):
        if hasattr(self, "http"):
            await self.http.create()

    async def cog_unload(self):
        if hasattr(self, "http"):
            await self.http.close()

    @classmethod
    async def setup(cls, bot: MasterBot):
        self = cls(bot)
        await bot.add_cog(self)


def command(**kwargs):
    def inner(coro):
        testing = kwargs.pop('testing', None)
        func = app_commands.command(**kwargs)(coro)
        if testing:
            func = app_commands.guilds(discord.Object(id=878431847162466354))(func)
        if not re.search(r'^[\w-]{1,32}$', func.name):
            raise ValueError(r'name must follow regex ^[\w-]{1,32}$')
        return func
    return inner


class NoPrivateMessage(app_commands.CheckFailure):
    def __init__(self, message=None):
        self.message = message or 'This command can only be used in a server.'
        super().__init__(message)


def app_guild_only():
    async def predicate(interaction):
        if interaction.guild:
            return True
        raise NoPrivateMessage()
    return app_commands.check(predicate)
