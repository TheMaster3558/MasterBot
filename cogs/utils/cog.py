from __future__ import annotations

from discord.ext import commands
from discord import app_commands
from cogs.utils.help_utils import HelpSingleton
from typing import ClassVar, TYPE_CHECKING

if TYPE_CHECKING:
    from bot import MasterBot


class CogMeta(type(commands.Cog)):
    def __new__(cls, *args, **kwargs):
        help_command = kwargs.pop('help_command', None)
        app_commands_group = kwargs.pop('app_commands_group', False)
        new_cls = super().__new__(cls, *args, **kwargs)  # type: ignore
        new_cls.help_command = help_command
        new_cls.app_commands_group = app_commands_group
        return new_cls


class Cog(commands.Cog, app_commands.Group, metaclass=CogMeta):
    help_command: ClassVar[HelpSingleton]
    app_commands_group: ClassVar[bool]
    app_commands_to_add: ClassVar[list] = []  # global cog list

    def __init__(self, bot: MasterBot):
        self.bot = bot
        if self.app_commands_group:
            app_commands.Group.__init__(self, name=self.__class__.__cog_name__.replace(' ', '').lower())

    @classmethod
    def setup(cls, bot: MasterBot):
        self = cls(bot)
        bot.add_cog(self)
        if self.app_commands_group:
            bot.tree.add_command(self, guild=bot.test_guild)

    @classmethod
    def app_command(cls, func):
        cls.app_commands_to_add.append(func)
        return func
