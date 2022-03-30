import discord
from discord import app_commands
from discord.ext import commands
import expr
from bot import MasterBot
import re
from typing import Type, TypeVar
from cogs.utils.app_and_cogs import Cog, command


N = TypeVar('N', int, float)


def evaluate(expression: str, /, *, cls: Type[expr.core.C] = expr.builtin.Decimal, **kwargs) -> expr.core.C:
    """Modified to fit needs better"""
    state = expr.create_state(**kwargs)
    result = state.evaluate(expression, cls=cls)
    del state
    return result


class StateGroup(app_commands.Group):
    def __init__(self, cog):
        self.cog = cog
        super().__init__(name='state', description='Modify a state to save variables.')

    @app_commands.command(description='Create the state')
    async def create(self, interaction, variables: str):
        variables, _ = self.cog.parse_for_vars(variables)
        self.cog.states[interaction.user.id] = variables

    @app_commands.command(description='Delete the state')
    async def delete(self, interaction):
        try:
            del self.cog.states[interaction.user.id]
        except KeyError:
            pass


class Math(Cog, name='botmath'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.parse_regex = re.compile(r'\w+ *= *\d+')
        self.states: dict[int, dict[str, N]] = {}
        print('Math cog loaded')

    async def cog_load(self):
        await super().cog_load()
        self.bot.tree.add_command(StateGroup(self))
    
    async def cog_unload(self):
        await super().cog_unload()
        self.bot.tree.remove_command('state')

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

    @commands.command(description='I can do some math for you.')
    async def math(self, ctx, *, expression: str):
        variables, expression = self.remove_vars(expression)
        if ctx.author.id in self.states:
            self.states[ctx.author.id].update(variables)
            variables = self.states[ctx.author]
        result = evaluate(expression, variables=variables)
        await ctx.reply(result, mention_author=False)

    @command(name='domath', description="I'll do some math for you!")
    @app_commands.describe(expression='The math expression')
    async def _math(self, interaction, expression: str):
        variables, expression = self.remove_vars(expression)
        if interaction.user.id in self.states:
            self.states[interaction.user].update(variables)
            variables = self.states[interaction.user.id]
        result = evaluate(expression, variables=variables)
        await interaction.response.send_message(result)

    @math.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('I need something to actually do math on.')
            return
        raise error

    @commands.group(description='Create a `state` to save variables across commands.')
    async def state(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Options are `{ctx.clean_prefix}state create` or `{ctx.clean_prefix}state delete`')

    @state.command(description='Create the state.')
    async def create(self, ctx, *, variables=''):
        variables, _ = self.parse_for_vars(variables)
        self.states[ctx.author.id] = variables

    @state.command(aliases=['del', 'destroy'], description='Destory that state')
    async def delete(self, ctx):
        try:
            del self.states[ctx.author.id]
        except KeyError:
            pass

    @commands.command(description='3.14')
    async def pi(self, ctx):
        await ctx.send(expr.pi)

    @commands.command(description='Get the value of **phi**')
    async def phi(self, ctx):
        await ctx.send(expr.phi)

    @commands.command(description='Get the value of **e**')
    async def e(self, ctx):
        await ctx.send(expr.e)


async def setup(bot: MasterBot):
    await Math.setup(bot)


