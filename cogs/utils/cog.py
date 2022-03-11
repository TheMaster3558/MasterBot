from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands
from cogs.utils.help_utils import HelpSingleton
import re
from typing import ClassVar, TYPE_CHECKING

if TYPE_CHECKING:
    from bot import MasterBot


class CogMeta(type(commands.Cog)):
    def __new__(cls, *args, **kwargs):
        help_command = kwargs.pop('help_command', None)
        new_cls = super().__new__(cls, *args, **kwargs)  # type: ignore
        new_cls.help_command = help_command
        return new_cls


class Cog(commands.Cog, metaclass=CogMeta):
    help_command: ClassVar[HelpSingleton]
    app_commands_group: ClassVar[bool]
    commands_to_add: ClassVar[list[app_commands.Command]] = []

    def __init__(self, bot: MasterBot):
        self.bot = bot

    @classmethod
    def setup(cls, bot: MasterBot):
        self = cls(bot)
        bot.add_cog(self)


def command(**kwargs):
    def inner(coro):
        func = app_commands.command(**kwargs)(coro)
        if kwargs.pop('testing', None):
            func = app_commands.guilds(discord.Object(id=878431847162466354))(func)
        if not re.search(r'^[\w-]{1,32}$', func.name):
            raise ValueError(r'name must follow regex ^[\w-]{1,32}$')
        return func
    return inner


