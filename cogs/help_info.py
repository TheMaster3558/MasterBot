import re
import sys

import discord
from discord import app_commands
from discord.ext import commands
from async_google_trans_new import __version__ as agtn_version
import aiohttp
import fuzzywuzzy

from bot import MasterBot
from cogs.utils.view import View
from cogs.utils.app_and_cogs import Cog


class InviteView(View):
    def __init__(self, bot):
        super().__init__()
        url = bot.oath_url
        self.add_item(discord.ui.Button(label="Click here!", url=url))


class HelpEmbed(discord.Embed):
    def __init__(self, bot, **kwargs):
        super().__init__(**kwargs)
        self.set_footer(text=f"{bot.user.name} Help Menu", icon_url=bot.user.avatar.url)


class HelpCommand(commands.HelpCommand):
    async def send_bot_help(
        self, mapping: dict[Cog, list[commands.Command | commands.Group]], /
    ) -> None:
        del mapping[None]  # type: ignore # Non cog commands
        embeds = [await self.send_cog_help(cog, send=False) for cog in mapping]

        last = 0
        for i in range(5, len(embeds), 5):
            await self.context.author.send(embeds=embeds[last:i])
            last = i

    async def sendcommand_help(
        self, command: commands.Command, /, *, send: bool = True
    ) -> discord.Embed | None:
        if not await command.can_run(self.context):
            return

        embed = discord.Embed(
            title=f"{command.qualified_name.capitalize()} Help",
            description=command.description or "No description",
        )
        embed.add_field(
            name="Syntax", value=f"```{self.get_command_signature(command)}```"
        )

        if send:
            channel = self.get_destination()
            await channel.send(embed=embed)

        return embed

    async def send_group_help(
        self, group: commands.Group, /, *, send: bool = True
    ) -> discord.Embed | None:
        if not await group.can_run(self.context):
            return

        embed = discord.Embed(
            title=f"{group.qualified_name.capitalize()} Help",
            description=f"`{self.get_command_signature(group)}`" + group.description
            or "No " "description",
        )
        for sub in group.walk_commands():
            embed.add_field(
                name=sub.name,
                value=f"`{self.get_command_signature(sub)}`\n " + sub.description
                or "No " "description",
            )

        if send:
            channel = self.get_destination()
            await channel.send(embed=embed)

        return embed

    async def send_cog_help(self, cog: Cog, /, *, send: bool = True) -> discord.Embed:
        embed = discord.Embed(title=f"{cog.qualified_name.capitalize()} Help")

        for cmd in cog.walk_commands():
            try:
                await cmd.can_run(self.context)
            except commands.CheckFailure:
                continue

            embed.add_field(
                name=cmd.qualified_name.capitalize(),
                value=f'`{self.get_command_signature(cmd)}`\n{cmd.description or "No description"}',
                inline=False,
            )

        if send:
            channel = self.get_destination()
            await channel.send(embed=embed)

        return embed

    async def command_not_found(self, string: str) -> str:
        message = f"I couldn't find the command `{string}`"

        close_commands = self.context.bot.possible_commands(self.context)  # type: ignore
        if len(close_commands) > 0:
            message += "\n`{}`".format("`\n`".join(close_commands))

        return message


class Help(Cog):
    mention_regex = None

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        bot.help_command = HelpCommand()
        print("Help and Info cog loaded")

    async def get_regex(self):
        await self.bot.wait_until_ready()
        self.mention_regex = re.compile(f"<@!?{self.bot.user.id}>")

    async def cog_load(self):
        await super().cog_load()
        self.bot.loop.create_task(self.get_regex())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.bot.is_ready():
            return
        if self.mention_regex.fullmatch(message.content):
            prefix = (await self.bot.get_prefix(message))[2]
            await message.reply(f"My prefix is `{prefix}`", mention_author=False)

    @commands.hybrid_command(description="Get the ws latency")
    async def ping(self, ctx):
        await ctx.send(f"Pong! `{str(round(self.bot.latency * 1000))}ms`")

    @commands.hybrid_command(description="Invite me!")
    async def invite(self, ctx):
        embed = discord.Embed(title=f"{self.bot.user.name} Invite")
        await ctx.author.send(embed=embed, view=InviteView(self.bot))

    @commands.hybrid_command(description="Some info about me.")
    async def info(self, ctx):
        embed = discord.Embed(title=f"{self.bot.user.name} Info")
        embed.add_field(
            name="Version Info",
            value=f"{self.bot.user.name} version {self.bot.__version__}\n"
            f'[Python {sys.version.split(" ")[0]}](https://www.python.org)\n'
            f"[discord.py {discord.__version__}](https://github.com/Rapptz/discord.py)\n"
            f"[async-google-trans-new {agtn_version}](https://github.com/Theelx/async-google-trans-new)\n"
            f"[aiohttp {aiohttp.__version__}](https://docs.aiohttp.org/en/stable/)\n"
            f"[fuzzywuzzy {fuzzywuzzy.__version__}](https://github.com/seatgeek/thefuzz)\n"
            f"Platform {sys.platform}\n",
        )
        embed.add_field(
            name="Stats",
            value=f"Servers: {len(self.bot.guilds)}\nMembers: {sum(guild.member_count for guild in self.bot.guilds)}",
        )
        await ctx.send(embed=embed)


async def setup(bot: MasterBot):
    await Help.setup(bot)
