from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands
import aiofiles

from cogs.utils.app_and_cogs import Cog
from bot import MasterBot


class Version(Cog, name="version"):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        print("Version cog loaded")

    @commands.command(
        aliases=["whatsnew"],
        description="Find out what came in a new update. Starts from 1.4.0",
    )
    async def new(
        self,
        ctx,
        version: Literal["1.4.0", "1.4.1", "1.4.2", "1.4.3", "1.5.0", "1.5.1", "1.6.0"],
    ):
        path = version.replace(".", "-")
        path += ".txt"
        path = "version/" + path

        try:
            async with aiofiles.open(path, "r") as v:
                embed = discord.Embed(title=version, description=await v.read())
        except FileNotFoundError:
            await ctx.send("That version was not found.")
            return

        await ctx.send(embed=embed)

    @new.error
    async def on_error(self, ctx, error):
        if isinstance(commands.BadLiteralArgument):
            await ctx.send("I couldn't find that version")
            return
        await self.bot.on_command_error(ctx, error)


async def setup(bot: MasterBot):
    await Version.setup(bot)
