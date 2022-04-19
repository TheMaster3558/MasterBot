import expr
from bot import MasterBot
import re
from typing import Type, TypeVar

import discord
from discord import app_commands
from discord.ext import commands

from cogs.utils.app_and_cogs import Cog


N = TypeVar("N", int, float)


def evaluate(
    expression: str, /, *, cls: Type[expr.core.C] = expr.builtin.Decimal, **kwargs
) -> expr.core.C:
    """Modified to fit needs better"""
    state = expr.create_state(**kwargs)
    result = state.evaluate(expression, cls=cls)
    del state
    return result


class Math(Cog, name="botmath"):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.parse_regex = re.compile(r"\w+ *= *[\d.]+")
        self.states: dict[int, dict[str, N]] = {}
        print("Math cog loaded")

    def parse_for_vars(self, expression):
        finds = self.parse_regex.findall(expression)
        variables = {}
        for find in finds:
            k, v = find.split("=")
            variables[k.strip()] = v.strip()
        return variables, finds

    def remove_vars(self, expression):
        variables, finds = self.parse_for_vars(expression)
        for find in finds:
            expression = expression.replace(find, "")
        return variables, expression

    @commands.hybrid_command(description="I can do some math for you.")
    async def math(self, ctx, *, expression: str):
        variables, expression = self.remove_vars(expression)
        if ctx.author.id in self.states:
            self.states[ctx.author.id].update(variables)
            variables = self.states[ctx.author]

        result = evaluate(expression, variables=variables)
        await ctx.reply(result, mention_author=False)

    @math.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("I need something to actually do math on.")
            return
        raise error

    @commands.hybrid_group(
        description="Create a `state` to save variables across commands."
    )
    async def state(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                f"Options are `{ctx.clean_prefix}state create` or `{ctx.clean_prefix}state delete`"
            )

    @state.command(description="Create the state.")
    @app_commands.describe(variables="The variables to start with")
    async def create(self, ctx, *, variables: str = ""):
        variables, _ = self.parse_for_vars(variables)
        self.states[ctx.author.id] = variables
        await ctx.send("Your state was created.", ephemeral=True)

    @state.command(aliases=["del", "destroy"], description="Destroy that state")
    async def delete(self, ctx):
        try:
            del self.states[ctx.author.id]
        except KeyError:
            pass
        await ctx.send("Your state was deleted", ephemeral=True)

    @commands.hybrid_command(description="3.14")
    async def pi(self, ctx):
        await ctx.send(expr.pi)

    @commands.hybrid_command(description="Get the value of phi")
    async def phi(self, ctx):
        await ctx.send(expr.phi)

    @commands.hybrid_command(description="Get the value of e")
    async def e(self, ctx):
        await ctx.send(expr.e)


async def setup(bot: MasterBot):
    await Math.setup(bot)
