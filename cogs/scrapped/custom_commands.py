import discord
from discord.ext import commands, tasks
from cogs.utils.app_and_cogs import Cog
from bot import MasterBot
import aiosqlite
from sqlite3 import IntegrityError
import asyncio
from typing import Optional, Tuple
import contextlib


class CommandCreateFlags(commands.FlagConverter):
    name: str
    output: str


class CustomCommands(Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.db = None
        self.cc: dict[int, list[commands.Command]] = {}
        print('Custom Commands cog loaded')

    async def cog_load(self):
        await super().cog_load()
        self.update_commands.start()

    async def cog_unload(self):
        await super().cog_unload()
        self.update_commands.cancel()

    @tasks.loop(minutes=9)
    async def update_commands(self):
        for guild in self.bot.guilds:
            if guild.id not in self.cc:
                continue

            _tasks = []

            cmds = self.cc[guild.id]
            for cmd in cmds:
                async def nest():
                    try:
                        await self.db.execute()
                    except IntegrityError:
                        await self.db.execute()
                _tasks.append(self.bot.loop.create_task(nest()))
            await asyncio.gather(*_tasks)

    @update_commands.before_loop
    async def before(self):
        await self.bot.wait_until_ready()
        self.db = aiosqlite.connect('cogs/databases/commands.db')
        _tasks = []

        for guild in self.bot.guilds:
            _tasks.append(self.bot.loop.create_task(self.db.execute()))
        await asyncio.gather(*_tasks)
        await self.db.commit()

    @update_commands.after_loop
    async def after(self):
        await self.update_commands()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ...

    @commands.command(aliases=['cc'])
    async def custom_command(self, ctx, *, flags: CommandCreateFlags):
        async def func(*args):
            ...


        msg: discord.Message = await ctx.send('Click ✅ to confirm', embed=...)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=lambda r, u: u == ctx.author and str(
                r.emoji
            ) in ('✅', '❌'), timeout=60)
        except asyncio.TimeoutError:
            await msg.reply('Cancelled')
        else:
            if str(reaction.emoji) == '❌':
                await msg.reply('Cancelled')
            else:
                if ctx.guild.id not in self.cc:
                    self.cc[ctx.guild.id] = []
                self.cc[ctx.guild.id].append(...)
                await ctx.send('Done!')

        with contextlib.suppress(discord.HTTPException):
            await msg.clear_reactions()


async def setup(bot: MasterBot):
    await bot.add_cog(CustomCommands(bot))



