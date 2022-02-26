import discord
from discord.ext import commands
import slash_util
import expr
from bot import MasterBot
import re
from typing import Type, TypeVar, Dict


UorM = TypeVar('UorM', bound=discord.User)
N = TypeVar('N', int, float)


def evaluate(expression: str, /, *, cls: Type[expr.core.C] = expr.builtin.Decimal, **kwargs) -> expr.core.C:
    """Modified to fit needs better"""
    state = expr.create_state(**kwargs)
    result = state.evaluate(expression, cls=cls)
    del state
    return result


class Math(slash_util.Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.parse_regex = re.compile('\w *= *\d+')
        self.states: Dict[UorM, Dict[str, N]] = {}
        print('Math cog loaded')

    def parse_for_vars(self, expression):
        finds = self.parse_regex.findall(expression)
        variables = {}
        for find in finds:
            k, v = find.split('=')
            variables[k.strip()] = v.strip()
        return variables, finds

    def remove_vars(self, expression):
        variables, finds = self.parse_for_vars(expression)
        for find in finds:
            expression = expression.replace(find, '')
        return variables, expression

    @commands.command()
    async def math(self, ctx, *, expression: str):
        variables, expression = self.remove_vars(expression)
        if ctx.author in self.states:
            self.states[ctx.author].update(variables)
            variables = self.states[ctx.author]
        result = evaluate(expression, variables=variables)
        await ctx.reply(result, mention_author=False)
        return

    @math.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('I need something to actually do math on.')
        raise error

    @commands.group()
    async def state(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Options are `{ctx.clean_prefix}state create` or `{ctx.clean_prefix}state delete`')

    @state.command()
    async def create(self, ctx, *, variables=''):
        variables, _ = self.parse_for_vars(variables)
        self.states[ctx.author] = variables

    @state.command(aliases=['del', 'destroy'])
    async def delete(self, ctx):
        del self.states[ctx.author]


def setup(bot: MasterBot):
    bot.add_cog(Math(bot))


