import discord
from discord.ext import commands
import slash_util
from bot import MasterBot
import re

from cogs.reaction_roles import ReactionRoles
from cogs.moderation import Moderation
from cogs.code import Code
from cogs.translate import Translator
from cogs.trivia import Trivia
from cogs.clash_royale import ClashRoyale
from cogs.jokes import Jokes
from cogs.webhook import Webhooks
from cogs.weather import Weather
from cogs.forms import Forms
from cogs.math import Math

import sys
from async_google_trans_new import __version__ as agtn_version
from importlib.metadata import version
import aiohttp
import fuzzywuzzy

from cogs.utils.view import View


class InviteView(View):
    def __init__(self, bot: MasterBot):
        super().__init__()
        url = bot.oath_url
        self.add_item(discord.ui.Button(label='Click here!', url=url))


class HelpAndInfo(slash_util.Cog):
    mention_regex = None

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.slash_util_version = version('slash_util')
        self.bot.loop.create_task(self.get_regex())
        print('Help and Info cog loaded')

    async def get_regex(self):
        await self.bot.wait_until_ready()
        self.mention_regex = re.compile(f'<@!?{self.bot.user.id}>')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.mention_regex.fullmatch(message.content):
            prefix = (await self.bot.get_prefix(message))[2]
            await message.reply(f'My prefix is `{prefix}`', mention_author=False)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! `{str(round(self.bot.latency * 1000))}ms`')

    @slash_util.slash_command(name='ping', description='Pong!')
    async def _ping(self, ctx):
        await self.ping(ctx)

    @commands.command()
    async def invite(self, ctx):
        embed = discord.Embed(title=f'{self.bot.user.name} Invite')
        await ctx.author.send(embed=embed, view=InviteView(self.bot))

    @slash_util.slash_command(name='invite', description='Invite me!')
    async def _invite(self, ctx):
        await ctx.send('Check ur DMs.')
        await self.invite(ctx)

    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(title=f'{self.bot.user.name} Info')
        embed.add_field(name='Version Info', value=f'{self.bot.user.name} version {self.bot.__version__}\n'
                                                  f'[Python {sys.version.split(" ")[0]}](https://www.python.org)\n'
                                                  f'[discord.py {discord.__version__}](https://github.com/Rapptz/discord.py)\n'
                                                  f'[slash_util {self.slash_util_version}](https://github.com/XuaTheGrate/slash_util)\n'
                                                  f'[async-google-trans-new {agtn_version}](https://github.com/Theelx/async-google-trans-new)\n'
                                                  f'[aiohttp {aiohttp.__version__}](https://docs.aiohttp.org/en/stable/)\n'
                                                  f'[fuzzywuzzy {fuzzywuzzy.__version__}](https://github.com/seatgeek/thefuzz)\n'
                                                  f'Platform {sys.platform}')
        embed.add_field(name='Stats', value=f'Servers: {len(self.bot.guilds)}\nUnique Users: {len(set(self.bot.users))}')
        await ctx.send(embed=embed)

    @slash_util.slash_command(name='info', description='Get info about the bot')
    async def _info(self, ctx):
        await self.info(ctx)

    @commands.group(name='help')
    async def _help(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title=f'{self.bot.user.name} Help Menu')
            embed.add_field(name='Categories',
                            value='`reactions`\n`moderation`\n`code`\n`translation`\n`trivia`\n`cr`(Clash Royale)\n`jokes`\n`webhook`\n`weather`\n`forms`\n`weather`')
            embed.add_field(name='Info', value=f'`{ctx.clean_prefix}info`')
            await ctx.send(embed=embed)

    @_help.command()
    async def reactions(self, ctx):
        prefix = ctx.clean_prefix
        h = ReactionRoles.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Reaction Role Help',
                              description=help_message)
        await ctx.send(embed=embed)

    @_help.command()
    async def moderation(self, ctx):
        prefix = ctx.clean_prefix
        h = Moderation.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Moderation Help',
                              description=help_message)
        await ctx.send(embed=embed)

    @_help.command()
    async def code(self, ctx):
        prefix = ctx.clean_prefix
        h = Code.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Code Help',
                              description=help_message)
        await ctx.send(embed=embed)

    @_help.command()
    async def translate(self, ctx):
        prefix = ctx.clean_prefix
        h = Translator.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Translate Help',
                              description=help_message)
        embed.set_footer(text='This bot uses Google Translate to do this')
        await ctx.send(embed=embed)

    @_help.command()
    async def trivia(self, ctx):
        prefix = ctx.clean_prefix
        h = Trivia.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Trivia Help',
                              description=help_message)
        embed.set_footer(text='This bot uses opentdb.com to do this')
        await ctx.send(embed=embed)

    @_help.command()
    async def cr(self, ctx):
        prefix = ctx.clean_prefix
        h = ClashRoyale.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Clash Royale Help',
                              description=help_message)
        embed.set_footer(text='This bot uses the Clash Royale API to do this. Learn more at developer.clashroyale.com')
        await ctx.send(embed=embed)

    @_help.command()
    async def jokes(self, ctx):
        prefix = ctx.clean_prefix
        h = Jokes.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Jokes Help',
                              description=help_message)
        embed.set_footer(text='This bot uses jokeapi.dev to do this')
        await ctx.send(embed=embed)

    @_help.command()
    async def webhook(self, ctx):
        prefix = ctx.clean_prefix
        h = Webhooks.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Webhook Help',
                              description=help_message)
        await ctx.send(embed=embed)

    @_help.command()
    async def weather(self, ctx):
        prefix = ctx.clean_prefix
        h = Weather.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Weather Help',
                              description=help_message)
        await ctx.send(embed=embed)

    @_help.command()
    async def forms(self, ctx):
        prefix = ctx.clean_prefix
        h = Forms.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Forms Help',
                              description=help_message)
        await ctx.send(embed=embed)

    @_help.command()
    async def math(self, ctx):
        prefix = ctx.clean_prefix
        h = Math.help_command(prefix)
        help_message = h.full_help()
        embed = discord.Embed(title='Math Help',
                              description=help_message)
        await ctx.send(embed=embed)

def setup(bot: MasterBot):
    bot.add_cog(HelpAndInfo(bot))
