from typing import Tuple, Optional, Iterable, Literal
import asyncio
import json

import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite

from bot import MasterBot
from cogs.utils.app_and_cogs import Cog
from cogs.utils.view import View


MISSING = discord.utils.MISSING


class RoleSelect(discord.ui.Select['RoleSelectView']):
    def __init__(
            self,
            items,
            *, mode: Literal[0, 1],
    ):
        options = [
            discord.SelectOption(label=role.name,
                                 emoji=emoji, value=str(role.id)) for role, emoji in items
        ]

        super().__init__(placeholder='Manage your roles', min_values=1, options=options, max_values=len(items))

        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        roles = [interaction.guild.get_role(int(role_id)) for role_id in self.values]
        if len(roles) == 0:
            names = ['no roles']
        else:
            names = [role.name for role in roles]

        word = 'Added' if self.mode == 0 else 'Removed'
        func = discord.Member.add_roles if self.mode == 0 else discord.Member.remove_roles

        await interaction.response.send_message(f'{word} {", ".join(names)}')
        await func(interaction.user, *roles)  # type: ignore


class RoleView(View):
    def __init__(self,
                 roles,
                 emojis):
        self.options = [(roles[i], emojis[i]) for i in range(len(roles) - 1)]

        super().__init__(timeout=None)

    @discord.ui.button(label='Add', style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        select = RoleSelect(self.options, mode=0)

        view = View()
        view.add_item(select)

        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.ui.button(label='Remove', style=discord.ButtonStyle.red)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        select = RoleSelect(self.options, mode=1)

        view = View()
        view.add_item(select)

        await interaction.response.send_message(view=view, ephemeral=True)


class RoleFlags(commands.FlagConverter):
    channel: Optional[discord.TextChannel] = commands.CurrentChannel
    roles: Tuple[discord.Role, ...]
    emojis: Optional[Tuple[discord.Emoji | discord.PartialEmoji | str, ...]] = []
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    color: Optional[discord.Color | int]


class ReactionRoles(Cog, name='reactions'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.db: aiosqlite.Connection = MISSING
        print('Roles cog loaded')

    async def fetch_from_db(self):
        cursor = await self.db.execute("""SELECT * FROM sqlite_master where type='table'""")
        tables = await cursor.fetchall()

        for table in tables:
            cursor = await self.db.execute(f"""SELECT * FROM {table}""")
            data = await cursor.fetchall()
            print(data)

    async def insert_into_db(self, roles, emojis, message_id):
        await self.db.execute(f"""CREATE TABLE IF NOT EXISTS {message_id} (
                                        useless INTEGER PRIMARY KEY,
                                        role INTEGER,
                                        emoji TEXT 
                                    );""")

    async def cog_load(self):
        await super().cog_load()
        self.db = await aiosqlite.connect('databases/roles.db')
        self.bot.loop.create_task(self.fetch_from_db())

    async def cog_unload(self):
        await super().cog_unload()
        await self.db.close()

    async def cog_command_error(self, ctx, error) -> None:
        error: commands.CommandError

        if isinstance(error, (commands.NoPrivateMessage, commands.MissingPermissions)):
            return
        await self.bot.on_command_error(ctx, error)

    @commands.command(description='Set up a select menu for a similar version of "Reaction Roles"')
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx: commands.Context, *, flags: RoleFlags):
        if len(flags.roles) > 25:
            msg = await ctx.send("You can't have more than 25 roles.")

            await asyncio.sleep(5)
            try:
                await msg.delete()
            except discord.NotFound:
                pass
            return

        embed = discord.Embed(title=flags.title, description=flags.description)

        if flags.image:
            if not flags.image.startswith('http://') or not flags.image.startswith('https://'):
                msg = await ctx.send(
                    'The image must start with `http://` or `https://`'
                )

                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except discord.NotFound:
                    pass
                return
            embed.set_image(url=flags.image)

        flags.emojis = list(flags.emojis)
        while len(flags.emojis) < len(flags.roles):
            flags.emojis.append(None)  # type: ignore

        while "None" in flags.emojis:
            index = flags.emojis.index("None")
            flags.emojis[index] = None  # type: ignore

        view = RoleView(flags.roles, flags.emojis)

        try:
            await flags.channel.send(embed=embed, view=view)
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to send messages in {flags.channel.mention}")


async def setup(bot: MasterBot):
    await ReactionRoles.setup(bot)
