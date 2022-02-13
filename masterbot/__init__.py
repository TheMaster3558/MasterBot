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


__title__ = 'masterbot'
__version__ = '1.0.0b'
__author__ = 'The Master'
__copyright__ = 'Copyright 2021-present The Master'
__license__ = 'MIT'
