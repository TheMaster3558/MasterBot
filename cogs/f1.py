from typing import Optional

import discord
from discord.ext import commands
import fastf1

from cogs.utils.app_and_cogs import Cog
from bot import MasterBot


class Formula1(Cog, name='formula one'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        fastf1.Cache.enable_cache('')
        print('Formula One cog loaded')

    @commands.command()
    async def race(self, *, name, year: Optional[int] = 2022):
        event = fastf1.get_event(year, name)
        print(dir(event))


async def setup(bot: MasterBot):
    await Formula1.setup(bot)

