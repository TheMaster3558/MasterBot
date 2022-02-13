"""
MasterBot
~~~~~~~~~
MasterBot is a Discord Bot created by The Master
It has a few cogs and development is still in progress

:copyright: (c) 2021-present The Master
:license: MIT
"""


from .bot import MasterBot, DatabaseFolderNotFound
from .cogs import cog_list
from .api_keys import MasterBotAPIKeyManager

from collections import namedtuple
from typing import Literal


__title__ = 'masterbot'
__version__ = '1.0.0b'
__author__ = 'The Master'
__copyright__ = 'Copyright 2021-present The Master'
__license__ = 'MIT'


class VersionInfo(namedtuple):
    major: int
    minor: int
    micro: int
    release: Literal["a", "b", "rc", "final"]


version_info = VersionInfo(major=1, minor=0, micro=0, release="a")
