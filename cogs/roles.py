import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot import MasterBot
from cogs.utils.app_and_cogs import Cog


class ReactionRoles(Cog, name='reactions'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        print('Roles cog loaded')


async def setup(bot: MasterBot):
    await ReactionRoles.setup(bot)
