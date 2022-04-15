from typing import Tuple, Optional, Literal
import asyncio
import string
import re

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
            guild: discord.Guild | None = None
    ):
        for index, data in enumerate(items):
            role, emoji = data

            if isinstance(role, discord.Object):
                new_role = guild.get_role(role.id)
                if new_role is None:
                    role.name = 'DELETED ROLE'
                    new_role = role

                items[index] = (new_role, emoji)

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

        await interaction.response.send_message(f'{word} {", ".join(names)}.', ephemeral=True)
        try:
            await func(interaction.user, *roles)  # type: ignore
        except discord.NotFound:
            await interaction.followup.send('The role was deleted.')


class RoleView(View):
    def __init__(self,
                 roles,
                 emojis,
                 *,
                 guild: discord.Guild | None = None):
        self.options = [(roles[i], emojis[i]) for i in range(len(roles) - 1)]
        self.guild = guild
        super().__init__(timeout=None)

    @discord.ui.button(label='Add', style=discord.ButtonStyle.green, custom_id='add')
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        select = RoleSelect(self.options, mode=0, guild=self.guild)

        view = View()
        view.add_item(select)

        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.ui.button(label='Remove', style=discord.ButtonStyle.red, custom_id='remove')
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        select = RoleSelect(self.options, mode=1, guild=self.guild)

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
    encoder = {str(num): let for num, let in enumerate(string.ascii_lowercase)}
    decoder = {let: num for num, let in enumerate(string.ascii_lowercase)}

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.db: aiosqlite.Connection = MISSING
        self.pending: dict = {}
        self.emoji_id = re.compile('[0-9]{15,20}')
        print('Roles cog loaded')

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.message.id not in self.pending:
            return

        pending = self.pending.pop(interaction.message.id)

        roles, emojis = [], []
        for role, emoji in pending:
            if emoji == 'None':
                emoji = None
            else:
                find = self.emoji_id.search(emoji)
                if find:
                    emoji = discord.Object(id=int(find.group()))

            roles.append(discord.Object(id=role))
            emojis.append(emoji)
        view = RoleView(roles, emojis, guild=interaction.guild)
        self.bot.add_view(view, message_id=interaction.message.id)

        if interaction.data['custom_id'] == 'add':
            await view.add.callback(interaction)
        elif interaction.data['custom_id'] == 'remove':
            await view.remove.callback(interaction)
        else:
            raise ValueError()

    async def fetch_from_db(self):
        async with self.db.execute("""SELECT * FROM sqlite_master where type='table'""") as cursor:
            tables = await cursor.fetchall()
            tables = [table for _, table, _, _, _ in tables]

            for table in tables:
                cursor = await self.db.execute(f"""SELECT * FROM {table}""")
                data = await cursor.fetchall()
                self.pending[self.decode(table)] = data  # view added on_interaction
                # we don't know where the message or role is until we get the channel and guild

    @classmethod
    def encode(cls, int_id) -> str:
        return ''.join(cls.encoder[char] for char in str(int_id))

    @classmethod
    def decode(cls, letters) -> int:
        return int(''.join(str(cls.decoder[char]) for char in letters))

    async def insert_into_db(self, roles, emojis, message_id):
        encoded = self.encode(message_id)

        cursor = await self.db.cursor()
        await cursor.execute(f"""CREATE TABLE IF NOT EXISTS {encoded} (
                                            role INTEGER,
                                            emoji TEXT 
                                        );""")
        for num, role in enumerate(roles):
            await cursor.execute(f"""INSERT INTO {encoded} VALUES (?, ?);""",
                                 (role.id, str(emojis[num])))

        await cursor.close()
        await self.db.commit()

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

        view = RoleView(flags.roles, flags.emojis, guild=ctx.guild)

        try:
            msg = await flags.channel.send(embed=embed, view=view)
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to send messages in {flags.channel.mention}")
        else:
            await self.insert_into_db(flags.roles, flags.emojis, msg.id)


async def setup(bot: MasterBot):
    await ReactionRoles.setup(bot)
