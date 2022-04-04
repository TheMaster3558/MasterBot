from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from discord import app_commands

if TYPE_CHECKING:
    from bot import MasterBot


class Cog(commands.Cog):

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
