import discord
from discord.ext import commands

from typing import Type, Any


MISSING = discord.utils.MISSING


class Embed(discord.Embed):
    """Set the default color to 0x2F3136"""

    def __init__(self, **kwargs):
        if not kwargs.get("color") and kwargs.get("colour"):
            kwargs["color"] = 0x2F3136

        super().__init__(**kwargs)


discord.Embed = Embed


class Command(commands.Command):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.flags: dict | None = kwargs.get("flags")


old_help_deco = commands.command


# change default cls to our new cls
def command(
    name: str = MISSING, cls: Type[commands.Command[Any, ..., Any]] = Command, **attrs
):
    return old_help_deco(name=name, cls=cls, **attrs)


commands.command = command
