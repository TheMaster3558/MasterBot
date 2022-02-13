"""
License: Apache License 2.0
2021-present The Master
See LICENSE for more
"""


import discord
from discord.ext import commands
import json


class Help:
    def __init__(self, prefix):
        self.prefix = prefix

    def welcome_set(self):
        message = f'`{self.prefix}welcome set join <message>`: Set the message for when users join\n' \
        f'`{self.prefix}welcome set leave <message>`: Set the message for when users leave\n' \
        f'`{self.prefix}welcome set channel <channel>`: Set the channel to send the messages to'
        return message

    def welcome_remove(self):
        message = f'`{self.prefix}welcome remove join`: Remove the join message\n' \
        f'`{self.prefix}welcome remove leave`: Remove the leave message\n' \
        f'`{self.prefix}welcome remove both`: Remove the join and leave message'
        return message

    def full_help(self):
        help_list = [self.welcome_set(), self.welcome_remove()]
        return '\n'.join(help_list) + '\n**Not available with Slash Commands.**'


def get_channel(bot, member):
    with open('welcomes.json', 'r') as c:
        channels = json.load(c)
    if channels.get(str(member.guild.id)):
        if channels[str(member.guild.id)] != 'off':
            return bot.get_channel(channels[str(member.guild.id)])
        return None
    return member.guild.system_channel


def get_join_message(member):
    with open('message.json', 'r') as m:
        messages = json.load(m)
    if messages.get(str(member.guild.id)):
        if messages[str(member.guild.id)] != 'off':
            return discord.Embed(title=f'Welcome to **{member.guild.name}**',
                                 description=messages[str(member.guild.id)])
        return None
    return discord.Embed(title=f'Welcome to **{member.guild.name}**',
                         description='We hope you have fun!')


def get_leave_message(member):
    with open('removes.json', 'r') as m:
        messages = json.load(m)
    if messages.get(str(member.guild.id)):
        if messages[str(member.guild.id)] != 'off':
            return messages[str(member.guild.id)]
        return None
    return 'See you later!'


class WelcomeMessages(commands.Cog):
    """
    Cog going bye bye in april
    """
    def __init__(self, bot):
        self.bot = bot
        print('Welcome Messages cog loaded')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.id == self.bot.user.id:
            return
        channel = get_channel(self.bot, member)
        if channel is not None:
            if channel.permissions_for(member.guild.me).send_messages:
                message = get_join_message(member)
                if message is not None:
                    await channel.send(member.mention,
                                       embed=message)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.id == self.bot.user.id:
            return
        channel = get_channel(self.bot, member)
        if channel is not None:
            if channel.permissions_for(member.guild.me).send_messages:
                message = get_leave_message(member)
                if message is not None:
                    await channel.send(message + f' {member.mention}')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with open('message.json', 'r') as m:
            messages = json.load(m)
        if messages.get(str(guild.id)):
            del messages[str(guild.id)]
            with open('message.json', 'w') as m:
                json.dump(messages, m)
        with open('removes.json', 'r') as m:
            messages = json.load(m)
        if messages.get(str(guild.id)):
            del messages[str(guild.id)]
            with open('removes.json', 'w') as m:
                json.dump(messages, m)
        with open('welcomes.json', 'r') as m:
            messages = json.load(m)
        if messages.get(str(guild.id)):
            del messages[str(guild.id)]
            with open('welcomes.json', 'w') as m:
                json.dump(messages, m)

    @commands.Cog.listener()
    async def on_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                return
            raise type(error)(error)
        else:
            raise type(error)(error)

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        pass

    @welcome.group(aliases=['create', 'add'])
    async def set(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title='Options',
                                  description='`join`\n`leave`\n`channel`')
            await ctx.send(embed=embed)

    @set.command()
    @commands.has_permissions(administrator=True)
    async def join(self, ctx, *, message):
        with open('message.json', 'r') as m:
            messages = json.load(m)
        messages[str(ctx.guild.id)] = message
        with open('message.json', 'w') as m:
            json.dump(messages, m)
        await ctx.send('Done!')

    @join.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title='You forgot something.',
                                  description=f'`{self.bot.command_prefix}join <message>`')
            await ctx.send(embed=embed)
        else:
            raise type(error)(error)

    @set.command()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx, *, message):
        with open('removes.json', 'r') as r:
            messages = json.load(r)
        if message != 'reset':
            messages[str(ctx.guild.id)] = message
        else:
            messages[str(ctx.guild.id)] = 'I hope you have fun!'
        with open('removes.json', 'w') as r:
            json.dump(messages, r)
        await ctx.send('Done!')

    @leave.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title='You forgot something.',
                                  description=f'`{self.bot.command_prefix}leave <message>`')
            await ctx.send(embed=embed)
        else:
            raise type(error)(error)

    @set.command()
    @commands.has_permissions(administrator=True)
    async def channel(self, ctx, *, channel: discord.TextChannel):
        with open('welcomes.json', 'r') as w:
            channels = json.load(w)
        channels[str(ctx.guild.id)] = channel.id
        with open('welcomes.json', 'w') as w:
            json.dump(channels, w)
        await ctx.send('Done!')

    @channel.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title='You forgot something.',
                                  description=f'`{ctx.prefix}channel <channel>`')
            await ctx.send(embed=embed)
        else:
            raise type(error)(error)

    @welcome.group(aliases=['off', 'stop'])
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title='Options',
                                  description='`join`\n`leave`\n`both`')
            await ctx.send(embed=embed)

    @remove.command(name='join')
    @commands.has_permissions(administrator=True)
    async def _join(self, ctx):
        with open('message.json') as w:
            messages = json.load(w)
        messages[str(ctx.guild.id)] = 'off'
        with open('message.json') as w:
            json.dump(messages, w)
        await ctx.send('Done!')

    @remove.command(name='leave')
    @commands.has_permissions(administrator=True)
    async def _leave(self, ctx):
        with open('removes.json', 'r') as w:
            removes = json.load(w)
        removes[str(ctx.guild.id)] = 'off'
        with open('removes.json', 'w') as w:
            json.dump(removes, w)
        await ctx.send('Done!')

    @remove.command()
    @commands.has_permissions(administrator=True)
    async def both(self, ctx):
        with open('welcomes.json', 'r') as w:
            channels = json.load(w)
        channels[str(ctx.guild.id)] = 'off'
        with open('welcomes.json', 'w') as w:
            json.dump(channels, w)
        await ctx.send('Done!')


def setup(bot: commands.Bot):
    bot.add_cog(WelcomeMessages(bot))
