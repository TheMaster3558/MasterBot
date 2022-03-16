import discord
from discord import app_commands
from discord.ext import commands
from bot import MasterBot

import re

import sys
from async_google_trans_new import __version__ as agtn_version
import aiohttp
import fuzzywuzzy

from cogs.utils.view import View
from cogs.utils.cog import Cog, command


class InviteView(View):
    def __init__(self, bot):
        super().__init__()
        url = bot.oath_url
        self.add_item(discord.ui.Button(label='Click here!', url=url))


class HelpEmbed(discord.Embed):
    def __init__(self, bot, **kwargs):
        super().__init__(**kwargs)
        self.set_footer(text=f'{bot.user.name} Help Menu', icon_url=bot.user.avatar.url)


class HelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping) -> None:
        embed = HelpEmbed(title=f'{self.context.bot.user.name} Help Menu',
                          bot=self.context.bot)
        embed.add_field(name='Categories',
                        value='`reactions`\t`moderation`\t`code`\t`translation`\t`trivia`\t`clashroyale`\t`jokes`\t`webhook`\t`weather`\t`forms`\t`weather`\t`math`\t`games`\t`version`')

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog: Cog) -> None:
        help_message = cog.help_command(self.context.clean_prefix).full_help()
        embed = HelpEmbed(title=f'{cog.qualified_name.capitalize()} Help',
                          description=help_message,
                          bot=self.context.bot)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, _command: commands.Command) -> None:
        cog = _command.cog
        if _command.root_parent:
            name = _command.root_parent.name
        else:
            name = _command.name
        help_message = getattr(cog.help_command, f'{name}_help')()

        embed = HelpEmbed(title=f'{_command.qualified_name.capitalize()} Help',
                          description=help_message,
                          bot=self.context.bot)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group: commands.Group) -> None:
        cog = group.cog
        help_message = getattr(cog.help_command, f'{group.name}_help')()

        embed = HelpEmbed(title=f'{group.name.capitalize()} Help',
                          description=help_message,
                          bot=self.context.bot)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def command_not_found(self, string: str) -> str:
        return f"I couldn't find the command \"{string}\""


class Help(Cog):
    mention_regex = None

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        bot.help_command = HelpCommand()
        print('Help and Info cog loaded')

    async def get_regex(self):
        await self.bot.wait_until_ready()
        self.mention_regex = re.compile(f'<@!?{self.bot.user.id}>')

    async def cog_load(self):
        await super().cog_load()
        self.bot.loop.create_task(self.get_regex())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.bot.is_ready():
            return
        if self.mention_regex.fullmatch(message.content):
            prefix = (await self.bot.get_prefix(message))[2]
            await message.reply(f'My prefix is `{prefix}`', mention_author=False)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! `{str(round(self.bot.latency * 1000))}ms`')

    @command(name='ping', description='Pong!')
    async def _ping(self, interaction):
        await interaction.response.send_message(f'Pong! `{str(round(self.bot.latency * 1000))}ms`')

    @commands.command()
    async def invite(self, ctx):
        embed = discord.Embed(title=f'{self.bot.user.name} Invite')
        await ctx.author.send(embed=embed, view=InviteView(self.bot))

    @command(name='invite', description='Invite me!')
    async def _invite(self, interaction):
        await interaction.response.send_message('Check ur DMs.')
        embed = discord.Embed(title=f'{self.bot.user.name} Invite')
        await interaction.user.send(embed=embed, view=InviteView(self.bot))

    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(title=f'{self.bot.user.name} Info')
        embed.add_field(name='Version Info', value=f'{self.bot.user.name} version {self.bot.__version__}\n'
                                                   f'[Python {sys.version.split(" ")[0]}](https://www.python.org)\n'
                                                   f'[discord.py {discord.__version__}](https://github.com/Rapptz/discord.py)\n'
                                                   f'[async-google-trans-new {agtn_version}](https://github.com/Theelx/async-google-trans-new)\n'
                                                   f'[aiohttp {aiohttp.__version__}](https://docs.aiohttp.org/en/stable/)\n'
                                                   f'[fuzzywuzzy {fuzzywuzzy.__version__}](https://github.com/seatgeek/thefuzz)\n'
                                                   f'Platform {sys.platform}')
        embed.add_field(name='Stats',
                        value=f'Servers: {len(self.bot.guilds)}\nUnique Users: {len(set(self.bot.users))}')
        await ctx.send(embed=embed)

    @command(name='info', description='Get info about the bot')
    async def _info(self, interaction):
        embed = discord.Embed(title=f'{self.bot.user.name} Info')
        embed.add_field(name='Version Info', value=f'{self.bot.user.name} version {self.bot.__version__}\n'
                                                   f'[Python {sys.version.split(" ")[0]}](https://www.python.org)\n'
                                                   f'[discord.py {discord.__version__}](https://github.com/Rapptz/discord.py)\n'
                                                   f'[async-google-trans-new {agtn_version}](https://github.com/Theelx/async-google-trans-new)\n'
                                                   f'[aiohttp {aiohttp.__version__}](https://docs.aiohttp.org/en/stable/)\n'
                                                   f'[fuzzywuzzy {fuzzywuzzy.__version__}](https://github.com/seatgeek/thefuzz)\n'
                                                   f'Platform {sys.platform}')
        embed.add_field(name='Stats',
                        value=f'Servers: {len(self.bot.guilds)}\nUnique Users: {len(set(self.bot.users))}')
        await interaction.response.send_message(embed=embed)


async def setup(bot: MasterBot):
    await Help.setup(bot)
