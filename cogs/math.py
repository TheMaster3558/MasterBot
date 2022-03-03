import discord
from discord.ext import commands
import slash_util
import expr
from bot import MasterBot
import re
from typing import Type, TypeVar, Dict, Literal
from cogs.utils.cog import Cog
from cogs.utils.help_utils import HelpSingleton


class Help(metaclass=HelpSingleton):
    def __init__(self, prefix):
        self.prefix = prefix

    def math_help(self):
        message = f'`{self.prefix}math <expression>`: Let me do some math for you!'
        return message

    def state_help(self):
        message = f'`{self.prefix}state create [vars]`: `vars` are optional. Create a state to save variables accross math commands!'
        message2 = f'`{self.prefix}state delete`: Delete that state.'
        return message + '\n' + message2

    def full_help(self):
        help_list = [self.math_help(), self.state_help()]
        return '\n'.join(help_list)


UserT = TypeVar('UserT', bound=discord.User)
N = TypeVar('N', int, float)


def evaluate(expression: str, /, *, cls: Type[expr.core.C] = expr.builtin.Decimal, **kwargs) -> expr.core.C:
    """Modified to fit needs better"""
    state = expr.create_state(**kwargs)
    result = state.evaluate(expression, cls=cls)
    del state
    return result


class Math(Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.parse_regex = re.compile('\w *= *\d+')
        self.states: Dict[UserT, Dict[str, N]] = {}
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

    @slash_util.slash_command(name='math', description="I'll do some math for you!")
    @slash_util.describe(expression='The math expression')
    async def _math(self, ctx, expression: str):
        await self.math(ctx, expression=expression)

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

    @slash_util.slash_command(name='state', description='Create a state to save variables when using /math')
    @slash_util.describe(option='"create" or "delete"', variables='Preset variables for your state')
    async def _state(self, ctx, option: Literal["create", "delete"], variables: str = ''):
        if option == 'create':
            await self.create(ctx, variables=variables)
        else:
            await self.delete(ctx)


def setup(bot: MasterBot):
    bot.add_cog(Math(bot))


