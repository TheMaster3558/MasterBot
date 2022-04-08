import asyncio
from typing import Tuple, Optional, Union
import json
from copy import deepcopy

import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot import MasterBot
from cogs.utils.app_and_cogs import Cog


class ReactionRoleFlags(commands.FlagConverter):
    title: Optional[str] = None
    names: Tuple[str, ...] = None
    emojis: Tuple[discord.Emoji | str, ...]
    roles: Tuple[discord.Role, ...]


class CustomReactionRoleFlags(commands.FlagConverter):
    title: Optional[Union[str]] = None
    description: Optional[str] = None
    emojis: Tuple[discord.Emoji | str, ...]
    roles: Tuple[discord.Role, ...]


class ReactionRoles(Cog, name='reactions'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.role_dict = {}
        print('Reaction Roles cog loaded')

    def _update(self):
        with open('databases/messages.json', 'w') as m:
            json.dump(self.role_dict, m, indent=2)

    @tasks.loop(seconds=30)
    async def update_file(self):
        async with self.bot.acquire_lock(self):  # type: ignore
            await asyncio.to_thread(self._update)

    @update_file.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    @update_file.after_loop
    async def after(self):
        await self.update_file()

    @commands.command(aliases=['rr', 'reactionrole'], description='Rework soon because it sucks!')
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def reaction_role(self, ctx, *, flags: ReactionRoleFlags):
        roles = flags.roles
        emojis = flags.emojis
        names = flags.names
        title = flags.title

        if len(emojis) != len(roles):
            msg = 'amount of emojis and roles should be the same'
            await ctx.send(msg)
            return

        for role in roles:
            if ctx.guild.roles.index(role) >= ctx.guild.roles.index(ctx.guild.me.top_role):
                msg = 'The role must be below my top role'
                await ctx.send(msg, delete_after=10)
                return

        if len(roles) > 15:
            await ctx.send('You must have 15 or under roles per reaction role message :|', delete_after=10)
            return

        if names is None:
            des = [f'{str(emojis[i])} = {str(roles[i].name)}' for i in range(0, len(roles))]
        else:
            des = [f'{str(emojis[i])} = {str(names[i])}' for i in range(0, len(names))]
        reaction_embed = discord.Embed(title=title or '',
                                       description=', '.join(des))
        message = await ctx.send(embed=reaction_embed)

        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
            except discord.errors.HTTPException:
                await ctx.send(
                    "Couldn't find one of the emojis 🤔. Make sure you only have 1 space separating them.",
                    delete_after=10
                )
                await message.delete()
                return
        d = {}
        for i in range(len(emojis)):
            if isinstance(emojis[i], str):
                d[emojis[i]] = roles[i].id
            else:
                d[emojis[i].id] = roles[i].id
        self.role_dict[str(message.id)] = {'emojis': d,
                                           'message': ctx.message.id}
        await ctx.message.delete()


async def setup(bot: MasterBot):
    await ReactionRoles.setup(bot)
