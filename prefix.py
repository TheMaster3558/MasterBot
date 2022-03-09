from __future__ import annotations

import discord
from discord.ext import commands, tasks
import json
from cogs.utils.cog import Cog

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import MasterBot


async def get_prefix(bot: MasterBot, msg: discord.Message) -> list[str]:
    prefixes = commands.when_mentioned(bot, msg)
    if msg.guild:
        _prefix = bot.prefixes.get(str(msg.guild.id), '!')
    else:
        _prefix = '!'
    prefixes.append(_prefix)
    return prefixes


class Prefix(Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.update_prefixes.start()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        del self.bot.prefixes[str(guild.id)]

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx: commands.Context, option):
        if option == 'reset':
            new_prefix = '!'
        else:
            new_prefix = option
        self.bot.prefixes[str(ctx.guild.id)] = new_prefix

    @prefix.error
    async def error(self, ctx, _error):
        if isinstance(_error, commands.MissingPermissions):
            await ctx.send('You need admin perms to change the prefix.')
        else:
            raise _error

    def fetch_prefixes(self):
        with open('databases/prefixes.json', 'r') as p:
            self.bot.prefixes = json.load(p)

    def update_file(self):
        with open('databases/prefixes.json', 'w') as p:
            json.dump(self.bot.prefixes, p)

    @tasks.loop(minutes=9)
    async def update_prefixes(self):
        async with self.bot.acquire_lock(self):
            await self.bot.loop.run_in_executor(None, self.update_file)

    @update_prefixes.before_loop
    async def before(self):
        await self.bot.wait_until_ready()
        await self.update_prefixes()

    @update_prefixes.after_loop
    async def after(self):
        await self.update_prefixes()
