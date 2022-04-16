import discord
from discord.ext import commands

from cogs.utils.app_and_cogs import Cog
from bot import MasterBot


class Chat(Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        print('Chat cog loaded')


async def setup(bot: MasterBot):
    await bot.add_cog(Chat(bot))
