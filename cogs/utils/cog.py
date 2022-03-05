import slash_util
from cogs.utils.help_utils import HelpSingleton
from typing import ClassVar


class CogMeta(type(slash_util.Cog)):
    def __new__(cls, *args, **kwargs):
        help_command = kwargs.pop('help_command', None)
        new_cls = super().__new__(cls, *args, **kwargs)  # type: ignore
        new_cls.help_command = help_command
        return new_cls


class Cog(slash_util.Cog, metaclass=CogMeta):
    help_command: ClassVar[HelpSingleton]
