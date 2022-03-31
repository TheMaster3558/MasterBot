import discord
from discord import app_commands
from discord.ext import commands
import PyDB as pydb
import aiosqlite


# databases directory must be changed
class EconomyDB(pydb.EconomyDB):
    async def connection(self) -> aiosqlite.core.Connection:
        return await sqlite.connect('databases/economy.db')
      
     
class LevelDB(pydb.LevelDB):
    async def connection(self) -> aiosqlite.core.Connection:
        return await sqlite.connect('databases/levels.db')


