import discord
from discord.ext import commands
from cogs.utils.cog import Cog, command
from bot import MasterBot
import aiofiles
from typing import Literal


class Version(Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        print('Version cog loaded')

    @commands.command(aliases=['whatsnew'])
    async def new(self, ctx, version):
        path = version.replace('.', '-')
        path += '.txt'
        path = 'version/' + path
        try:
            async with aiofiles.open(path, 'r') as v:
                embed = discord.Embed(title=version,
                                      description=await v.read())
        except FileNotFoundError:
            await ctx.send('That version was not found.')
            return
        await ctx.send(embed=embed)

    @command(name='whatsnew', description='Findout whats new in a version! Starts for 1.4.0', testing=True)
    async def _new(self, interaction, version: Literal[
        "1.4.0",
        "1.4.1"
    ]):
        path = version.replace('.', '-')
        path += '.txt'
        path = 'version/' + path
        try:
            async with aiofiles.open(path, 'r') as v:
                embed = discord.Embed(title=version,
                                      description=await v.read())
        except FileNotFoundError:
            await interaction.response.send_message('That version was not found.')
            return
        await interaction.response.send_message(embed=embed)


def setup(bot: MasterBot):
    Version.setup(bot)




