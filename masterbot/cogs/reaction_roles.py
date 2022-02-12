import discord
from discord.ext import commands, tasks
import asyncio
from typing import Tuple, Optional, Union
import json
import copy as c
import slash_util
from masterbot.bot import MasterBot


class Help:
    def __init__(self, prefix):
        self.prefix = prefix

    def reaction_roles_help(self):
        message = f'`{self.prefix}reactionrole`: Alias = `{self.prefix}rr`. Create a reaction role!' + f'\nArguments:\n\t`title` (optional)\n\t`names` (optional, roles names ' \
        f'will replace)\n\t`emojis`\n\t`roles`\n Example: `{self.prefix}rr title: ' \
        f'Hi! names: Red Green Blue emojis: ❤ 💚 💙 roles: RedRole GreenRole ' \
        f'Blue Role`'
        return message

    def custom_reaction_roles_help(self):
        message = f'`{self.prefix}customreactionrole`: Alias = `{self.prefix}crr`. Create a customreaction role!' + f'\nArguments:\n\t`title` (optional)\n\t`description` (optional)' \
        f'\n\t`emojis`\n\t`roles`\n Example: `{self.prefix}rr title: ' \
        f'Hi! description: react to get a color role! emojis: ❤ 💚 💙 roles: RedRole GreenRole ' \
        f'Blue Role`'
        return message

    def delete_help(self):
        message = f'`{self.prefix}delete <message>`: Delete a reaction role message.\nExample: `{self.prefix}delete 926567187550994434`'
        return message

    def full_help(self):
        help_list = [self.reaction_roles_help(), self.custom_reaction_roles_help(), self.delete_help()]
        return '\n'.join(help_list) + '\nNot available with Slash Commands.'


class ReactionRoleFlags(commands.FlagConverter):
    title: Optional[str] = None
    names: Tuple[str, ...] = None
    emojis: Tuple[Union[discord.Emoji, str], ...]
    roles: Tuple[discord.Role, ...]


class CustomReactionRoleFlags(commands.FlagConverter):
    title: Optional[Union[str, bool]] = None
    description: Optional[Union[str, bool]] = None
    emojis: Tuple[Union[discord.Emoji, str], ...]
    roles: Tuple[discord.Role, ...]


class ReactionRoles(commands.Cog):
    def __init__(self, bot: MasterBot):
        self.bot = bot
        with open('databases/messages.json', 'r') as m:
            self.role_dict = json.load(m)
        print('Reaction Roles cog loaded')
        self.update_file.start()

    async def convert_all(self, message):
        ctx = await self.bot.get_context(message)
        copy = c.deepcopy(self.role_dict)
        copy = copy[str(message.id)]
        copy: dict = copy.get('emojis')
        original_keys = list(copy.keys())
        for i in range(len(copy)):
            try:
                k = list(copy.keys())
                k = k[i]
                k = await commands.EmojiConverter().convert(ctx, str(k))
            except commands.EmojiNotFound or TypeError:
                k = list(copy.keys())[i]
            v = list(copy.values())
            v = v[i]
            v = await commands.RoleConverter().convert(ctx, str(v))
            copy[k] = v
        for key in original_keys:
            if isinstance(key, int):
                del copy[key]
        return copy

    def _update(self):
        with open('databases/messages.json', 'w') as m:
            json.dump(self.role_dict, m, indent=2)

    @tasks.loop(seconds=30)
    async def update_file(self):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._update)

    @update_file.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    @update_file.after_loop
    async def after(self):
        await self.update_file()

    @commands.command(aliases=['rr', 'reactionrole'])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def reaction_role(self, ctx, *, flags: ReactionRoleFlags):
        roles = flags.roles
        emojis = flags.emojis
        names = flags.names
        title = flags.title
        if len(emojis) != len(roles):
            embed = discord.Embed(title='amount of emojis and roles should be the same')
            return await ctx.send(embed=embed)
        for role in roles:
            if ctx.guild.roles.index(role) >= ctx.guild.roles.index(ctx.guild.me.top_role):
                embed = discord.Embed(title='The role must be below my top role')
                return await ctx.send(embed=embed, delete_after=10)
        if len(roles) > 10:
            embed = discord.Embed(title='You must have 10 or under roles per reaction role message :|')
            return await ctx.send(embed=embed, delete_after=10)
        if names is None:
            des = [f'{str(emojis[i])} = {str(roles[i].name)}' for i in range(0, len(roles))]
        else:
            des = [f'{str(emojis[i])} = {str(names[i])}' for i in range(0, len(names))]
        reaction_embed = discord.Embed(title=title or '',
                                       description=' '.join(des))
        message = await ctx.send(embed=reaction_embed)
        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
            except discord.errors.HTTPException:
                embed = discord.Embed(title="Couldn't find one of the emojis 🤔")
                await ctx.send(embed=embed, delete_after=10)
                return await message.delete()
        d = {}
        for i in range(len(emojis)):
            if isinstance(emojis[i], str):
                d[emojis[i]] = roles[i].id
            else:
                d[emojis[i].id] = roles[i].id
        self.role_dict[str(message.id)] = {'emojis': d,
                                           'message': ctx.message.id}
        await ctx.message.delete()

    @reaction_role.error
    async def error(self, ctx, error):
        if isinstance(error, commands.errors.RoleNotFound):
            embed = discord.Embed(title='1 or more of the roles was not found. 🤔')
            await ctx.send(embed=embed, delete_after=10)
        elif isinstance(error, commands.errors.MissingPermissions):
            pass
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(title="I don't have the permissions!? Give me manage_roles please")
            embed.set_footer(icon_url='https://cdn.discordapp.com/emojis/923067534792589312.png?size=96')
            await ctx.send(embed=embed, delete_after=10)
        elif isinstance(error, (commands.MissingRequiredArgument, commands.MissingFlagArgument)):
            if isinstance(self.bot.command_prefix, str):
                prefix = self.bot.command_prefix
            elif isinstance(self.bot.command_prefix, list):
                prefix = self.bot.command_prefix[2]
            else:
                prefix = '[p]'
            embed = discord.Embed(title='You have bad format',
                                  description=f'Arguments:\n\t`title` (optional)\n\t`names` (optional, roles names '
                                              f'will replace)\n\t`emojis`\n\t`roles`\n Example: `{prefix}rr title: '
                                              f'Hi! names: Red Green Blue emojis: ❤ 💚 💙 roles: RedRole GreenRole '
                                              f'Blue Role`')
            embed.set_footer(text='Do not make me say this again!')
            await ctx.send(embed=embed, delete_after=30)
        else:
            raise type(error)(error)

    @slash_util.slash_command(name='reaction role', description='Learn about how to make a reaction role message.')
    async def _reaction_role(self, ctx: slash_util.Context):
        embed = discord.Embed(title="Sorry but this won't work",
                              description="Slash Commands are different than normal commands." \
                              "The user input is much different. Message commands use flags." \
                              "Flags don't really work well in Slash Commands" \
                              f"Use {ctx.bot.name} as the prefix and do the `rr` command." \
                              "Sorry but it's easier for both me and you.")
        await ctx.send(embed=embed)

    @commands.command(aliases=['crr', 'customreactionrole'])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def custom_reaction_role(self, ctx, *, flags: CustomReactionRoleFlags):
        title = flags.title
        roles = flags.roles
        emojis = flags.emojis
        description = flags.description
        if len(emojis) != len(roles):
            embed = discord.Embed(title='amount of emojis and roles should be the same')
            return await ctx.send(embed=embed)
        for role in roles:
            if ctx.guild.roles.index(role) >= ctx.guild.roles.index(ctx.guild.me.top_role):
                embed = discord.Embed(title='The role must be below my top role')
                return await ctx.send(embed=embed, delete_after=10)
        if len(roles) > 10:
            embed = discord.Embed(title='You must have 10 or under roles per reaction role message :|')
            return await ctx.send(embed=embed, delete_after=10)
        reaction_embed = discord.Embed(title=title or '',
                                       description=description or '')
        message = await ctx.send(embed=reaction_embed)
        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
            except discord.errors.HTTPException:
                embed = discord.Embed(title="Couldn't find one of the emojis 🤔",
                                      description='Make sure only **1** space is separating them')
                await ctx.send(embed=embed, delete_after=10)
                return await message.delete()
        d = {}
        for i in range(len(emojis)):
            if isinstance(emojis[i], str):
                d[emojis[i]] = roles[i].id
            else:
                d[emojis[i].id] = roles[i].id
        self.role_dict[str(message.id)] = {'emojis': d,
                                           'message': ctx.message.id}
        await ctx.message.delete()

    @custom_reaction_role.error
    async def error(self, ctx, error):
        if isinstance(error, commands.errors.RoleNotFound):
            embed = discord.Embed(title='1 or more of the roles was not found. 🤔')
            await ctx.send(embed=embed, delete_after=10)
        elif isinstance(error, commands.errors.MissingPermissions):
            pass
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(title="I don't have the permissions!? Give me manage_roles please")
            embed.set_footer(icon_url='https://cdn.discordapp.com/emojis/923067534792589312.png?size=96')
            await ctx.send(embed=embed, delete_after=10)
        elif isinstance(error, (commands.MissingRequiredArgument, commands.MissingFlagArgument)):
            if isinstance(self.bot.command_prefix, str):
                prefix = self.bot.command_prefix
            elif isinstance(self.bot.command_prefix, list):
                prefix = self.bot.command_prefix[2]
            else:
                prefix = '[p]'
            embed = discord.Embed(title='You have bad format',
                                  description=f'Arguments:\n\t`title` (optional)\n\t`description` (optional)'
                                              f'\n\t`emojis`\n\t`roles`\n Example: `{prefix}rr title: '
                                              f'Color! description: react to get a color role!: ❤ 💚 💙 roles: '
                                              f'RedRole GreenRole Blue Role`')
            embed.set_footer(text='Do not make me say this again!')
            await ctx.send(embed=embed, delete_after=30)
        else:
            raise type(error)(error)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await asyncio.sleep(0.3)
        if str(payload.message_id) not in list(self.role_dict.keys()):
            return
        if payload.member.id == self.bot.user.id:
            return
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        data = await self.convert_all(message)
        message_emojis = data.copy()
        try:
            emoji = await commands.EmojiConverter().convert(await self.bot.get_context(message), str(payload.emoji))
        except commands.errors.EmojiNotFound:
            emoji = str(payload.emoji)
        if emoji not in message_emojis.keys():
            return await message.clear_reaction(emoji)
        my_dict = {}
        for k, v in message_emojis.items():
            if not isinstance(k, str):
                my_dict[id(k)] = v
            else:
                my_dict[k] = v
        try:
            role = my_dict[id(emoji)]
        except KeyError:
            role = my_dict[emoji]
        if role not in payload.member.roles:
            await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await asyncio.sleep(0.3)
        member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
        if member.id == self.bot.user.id:
            return
        if str(payload.message_id) not in list(self.role_dict.keys()):
            return
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        data = await self.convert_all(message)
        message_emojis = data
        try:
            emoji = await commands.EmojiConverter().convert(await self.bot.get_context(message), str(payload.emoji))
        except commands.errors.EmojiNotFound:
            emoji = str(payload.emoji)
        print(self.role_dict)
        my_dict = {}
        for k, v in message_emojis.items():
            if not isinstance(k, str):
                my_dict[id(k)] = v
            else:
                my_dict[k] = v
        print(self.role_dict)
        try:
            role = my_dict[id(emoji)]
        except KeyError:
            role = my_dict[emoji]
        if role in member.roles:
            await member.remove_roles(role)

    @commands.command()
    async def delete(self, ctx, message: discord.Message):
        if message.author.id != ctx.author.id:
            return
        if message.guild.id != ctx.guild.id:
            embed = discord.Embed(title='Try using the command in the server the message is in')
            return await ctx.send(embed=embed, delete_after=10)
        try:
            self.role_dict.pop(str(message.id))
        except KeyError:
            pass

    @delete.error
    async def error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed(title="Where's the message!? I can't find it without the link or ID")
            await ctx.send(embed=embed)


def setup(bot: MasterBot):
    bot.add_cog(ReactionRoles(bot))
