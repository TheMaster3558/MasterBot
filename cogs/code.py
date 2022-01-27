import os
import sys

import discord
from discord.ext import commands
import inspect
from typing import Optional
import random
import math
import re
import os as __os__  # to keep eval command safe
import sys as __sys__
import slash_util


class Help:
    def __init__(self, prefix):
        self.prefix = prefix

    def eval_help(self):
        message = f'`{self.prefix}eval <code>`: Code in python with the discord bot! (Command may not work). (Certain words will cause the code to not run to protect our system. [Click here for more](https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html))'
        return message

    def canrun_help(self):
        message = f'`{self.prefix}canrun [user] <command>`: User is optional. Check if you or the user can run the command.'
        return message

    def search_help(self):
        message = f'`{self.prefix}search <regex> <text>`: Use regular expressions `re.search()`. Example: `!search [a-z][0-9][A-Z] a0Z`'
        return message

    def match_help(self):
        message = f'`{self.prefix}match <regex> <text>`: Use regular expressions `re.fullmatch()`. Same as `search` but full match.'
        return message

    def full_help(self):
        help_list = [self.eval_help(), self.canrun_help(), self.search_help(), self.match_help()]
        return '\n'.join(help_list)


class Code(slash_util.ApplicationCog):
    """
    Many of the commands are owner only
    """
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        print('Code cog loaded')

    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command(name='eval', aliases=['e'])
    async def _eval(self, ctx, *, arg: str):
        """
        This command will need lots of working on.
        """
        if '__' in arg or 'os' in arg or 'bot' in arg:
            return
        dup = list(arg)
        dup.reverse()
        if arg.startswith('```') and ''.join(dup).startswith('```'):
            arg = list(arg)
            del arg[0]
            del arg[0]
            del arg[0]
            del arg[-1]
            del arg[-1]
            del arg[-1]
            arg = ''.join(arg)
        elif arg.startswith('```py') and ''.join(dup).startswith('```'):
            arg = list(arg)
            del arg[0]
            del arg[0]
            del arg[0]
            del arg[0]
            del arg[0]
            del arg[-1]
            del arg[-1]
            arg = ''.join(arg)
        elif arg.startswith('`') and ''.join(dup).startswith('`'):
            arg = list(arg)
            del arg[0]
            del arg[-1]
            arg = ''.join(arg)
        res = exec(arg, {'math': math, 'random': random, 're': re})
        if inspect.isawaitable(res):
            sendable = str(await res)
            if len(sendable) > 0:
                await ctx.send('```py\n{}\n```'.format(sendable))
        else:
            sendable = str(res)
            if len(sendable) > 0:
                await ctx.send('```py\n{}\n```'.format(sendable))

    @_eval.error
    async def error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Patience. Wait {:.1f}'.format(error.retry_after))
        else:
            await ctx.send('Command raised an exception\n```{}```'.format(error))

    @commands.command()
    async def canrun(self, ctx, user: Optional[discord.Member], *, acommand):
        command: commands.Command = self.bot.all_commands.get(acommand)
        if command is None:
            embed = discord.Embed(title=f'Command `{acommand}` not found.')
            return await ctx.send(embed=embed)
        ctx.author = user or ctx.author
        await command.can_run(ctx)
        await ctx.send('You can run this command!')

    @canrun.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title='Your too weak!',
                                  description=str(error))
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title='Missing something',
                                  description=f'`{self.bot.command_prefix}canrun [user] <command>`')
            await ctx.send(embed=embed)
        elif isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            await ctx.send("I couldn't find that person =(")
        else:
            raise type(error)(error)

    @commands.command()
    async def search(self, ctx, what, *, text):
        returned = re.search(what, text)
        await ctx.send(bool(returned))

    @slash_util.slash_command(name='search', description='Use regex to search text')
    @slash_util.describe(regex='The regular expression', text='The text to search.')
    async def _search(self, ctx, regex: str, text: str):
        await self.search(ctx=ctx, what=regex, text=text)

    @commands.command()
    async def match(self, ctx, what, *, text):
        returned = re.fullmatch(what, text)
        await ctx.send(bool(returned))

    @slash_util.slash_command(name='match', description='Use regex to match text')
    @slash_util.describe(regex='The regular expression', text='The text to match.')
    async def _match(self, ctx, regex: str, text: str):
        await self.match(ctx=ctx, what=regex, text=text)

    @commands.command()
    @commands.is_owner()
    async def logger(self, ctx, last=5):
        with open('discord.log', 'r') as l:
            log = l.read()
        log = log.split('\n')
        log.reverse()
        full = [log[i] for i in range(1, last)]
        legnth = [i for i in range(len(log)-last, len(log))]
        lined = '\n'.join(f'Line {legnth[i]}: {full[i]}' for i in range(len(full)))
        await ctx.send('```\n{}\n```'.format(lined))

    @commands.command(name='os')
    @commands.is_owner()
    async def _os(self, ctx, *, what):
        __os__.system(what)

    @commands.command()
    @commands.is_owner()
    async def close(self, ctx):
        await ctx.send('Closing. Bye bye!')
        await self.bot.close()
        __sys__.exit()


def setup(bot: commands.Bot):
    bot.add_cog(Code(bot))


