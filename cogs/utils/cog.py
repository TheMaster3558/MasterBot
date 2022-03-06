from discord.ext import commands
from discord import app_commands
from cogs.utils.help_utils import HelpSingleton
from typing import ClassVar
from bot import MasterBot


class CogMeta(type(commands.Cog)):
    def __new__(cls, *args, **kwargs):
        help_command = kwargs.pop('help_command', None)
        new_cls = super().__new__(cls, *args, **kwargs)  # type: ignore
        new_cls.help_command = help_command
        return new_cls


class Cog(commands.Cog, app_commands.Group, metaclass=CogMeta):
    help_command: ClassVar[HelpSingleton]

    def __init__(self, bot: MasterBot):
        self.bot = bot
        app_commands.Group.__init__(self, name=self.__class__.__cog_name__)
        self.name = self.__class__.__cog_name__.replace(' ', '').lower()

