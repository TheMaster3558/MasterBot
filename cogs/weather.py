from typing import Optional, Literal

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
from aiosqlite import IntegrityError

from cogs.utils.http import AsyncHTTPClient
from cogs.utils.weather_utils import WeatherUtils
from cogs.utils.app_and_cogs import Cog
from bot import MasterBot


class FlagUnits(commands.FlagConverter):
    speed: Optional[str] = None
    temp: Optional[str] = None


class WeatherAPIHTTPClient(AsyncHTTPClient):
    def __init__(self, api_key, loop):
        super().__init__('http://api.weatherapi.com/v1/', loop=loop)
        self.api_key = api_key

    async def request(self, route, json=True, **params):
        return await super().request(route=route,
                                     json=json,
                                     key=self.api_key,
                                     **params)

    async def current(self, location):
        return await self.request('current.json', q=location, aqi='no')

    async def forecast(self, location, days):
        return await self.request('forecast.json', q=location, days=days)

    async def search(self, query):
        return await self.request('search.json', q=query)

    async def timezone(self, location):
        return await self.request('timezone.json', q=location)


class Weather(Cog, name='weather'):
    metric = {'temp': 'C', 'speed': 'kph'}
    customary = {'temp': 'F', 'speed': 'mph'}

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.api_key = self.bot.weather
        self.http = WeatherAPIHTTPClient(self.api_key, self.bot.loop)
        self.temp_units = {}
        self.speed_units = {}
        self.db = None
        print('Weather cog loaded')
    
    async def cog_load(self):
        await super().cog_load()
        self.update_db.start()
    
    async def cog_unload(self):
        await super().cog_unload()
        self.update_db.cancel()

    async def fetch_units(self):
        for guild in self.bot.guilds:
            async with self.db.execute(f"""SELECT temp, speed FROM units
                                        WHERE id = {guild.id};""") as cursor:
                data = await cursor.fetchone()
            if data is None:
                continue

            temp, speed = data
            self.temp_units[guild.id] = temp
            self.speed_units[guild.id] = speed

    @tasks.loop(minutes=3)
    async def update_db(self):
        for guild in self.bot.guilds:
            if guild.id not in self.temp_units:
                self.temp_units[guild.id] = self.metric['temp']
            if guild.id not in self.speed_units:
                self.speed_units[guild.id] = self.metric['speed']
            try:
                await self.db.execute(f"""INSERT INTO units VALUES ({guild.id},
                '{self.temp_units[guild.id]}',
                '{self.speed_units[guild.id]}')""")
            except IntegrityError:
                await self.db.execute(f"""UPDATE units
                SET temp = '{self.temp_units[guild.id]}', speed = '{self.speed_units[guild.id]}'
                WHERE id = {guild.id};""")
        await self.db.commit()

    @update_db.before_loop
    async def before(self):
        await self.bot.wait_until_ready()
        self.db = await aiosqlite.connect('cogs/databases/units.db')
        await self.db.execute("""CREATE TABLE IF NOT EXISTS units (
                                        id INTEGER PRIMARY KEY,
                                        temp TEXT,
                                        speed TEXT
                                    );""")
        await self.db.commit()
        await self.fetch_units()

    @update_db.after_loop
    async def after(self):
        await self.update_db()
        await self.db.close()

    async def cog_command_error(self, ctx, error):
        error: commands.CommandError

        if not ctx.command:
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'You missed an argument "{error.param}"')
        else:
            if not ctx.command.has_error_handler():
                await self.bot.on_command_error(ctx, error)

    @commands.command(description='Change the units to use for weather.')
    @commands.has_permissions(administrator=True)
    async def units(self, ctx, *, flags: FlagUnits | str = None):
        if isinstance(flags, FlagUnits):
            if not flags.temp and not flags.speed:
                await ctx.send(
                    f'You forgot the flag arguments. `{ctx.prefix}units <flags_args>`. **Args:**\n`temp` `C` or '
                    f'`F`\n`speed` `mph` or `kph`` '
                )
                return

            if flags.temp:
                if flags.temp.upper() in ('C', 'F'):
                    self.temp_units[ctx.guild.id] = flags.temp.upper()
                else:
                    return await ctx.send('Temp can only be **c** or **f**')

            if flags.speed:
                if flags.speed.lower() in ('mph', 'kph'):
                    self.speed_units[ctx.guild.id] = flags.speed.lower()
                else:
                    return await ctx.send('Speed can only be **kph** or **mph**')

        elif isinstance(flags, str):
            if flags == 'metric':
                self.temp_units[ctx.guild.id] = self.metric['temp']
                self.speed_units[ctx.guild.id] = self.metric['speed']
            else:
                self.temp_units[ctx.guild.id] = self.customary['temp']
                self.speed_units[ctx.guild.id] = self.customary['speed']

        else:
            await ctx.send(
                f'You forgot the flag arguments. `{ctx.prefix}units <flags_args>`. **Args:**\n`temp` `C` or '
                f'`F`\n`speed` `mph` or `kph`` '
            )
            return

        await ctx.send(f'New settings! Temp: `{self.temp_units[ctx.guild.id]}` Speed: `{self.speed_units[ctx.guild.id]}`')

    @app_commands.command(name='units', description='Change the weather units')
    @app_commands.describe(temp='The temperature unit', speed='The speed unit')
    async def _units(self, interaction: discord.Interaction, temp: Literal["C", "F"] = None, speed: Literal["kph", "mph"] = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('You need admin perms.')
            return

        if not temp and not speed:
            await interaction.response.send_message('You must give at least one argument.')
            return

        if temp:
            if temp.upper() in ('C', 'F'):
                self.temp_units[interaction.guild.id] = temp.upper()
            else:
                return await interaction.response.send_message('Temp can only be **c** or **f**')

        if speed:
            if speed.lower() in ('mph', 'kph'):
                self.speed_units[interaction.guild.id] = speed.lower()
            else:
                await interaction.response.send_message('Speed can only be **kph** or **mph**')
                return

    @units.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Sorry. You need admin perms to change the units.')
        else:
            raise error

    @commands.command(description='Get the current weather of a place.')
    async def current(self, ctx, *, location):
        data = await self.http.current(location)
        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            await ctx.send(embed=error)
            return

        embed = await WeatherUtils.build_current_embed(data, ctx, self)
        if embed is None:
            return
        await ctx.send(embed=embed)

    @app_commands.command(name='current', description='Get the current weather of a location')
    @app_commands.describe(location='The location')
    async def _current(self, interaction, location: str):
        data = await self.http.current(location)
        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            await interaction.response.send_message(embed=error)
            return

        embed = await WeatherUtils.build_current_embed(data, interaction, self)
        if embed is None:
            return
        await interaction.response.send_message(embed=embed)

    @commands.command(description='Get the forcast of a place.')
    async def forecast(self, ctx, days: Optional[int] = 1, *, location):
        data = await self.http.forecast(location, days)

        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            await ctx.send(embed=error)
            return

        embed = await WeatherUtils.build_forecast_embed(data, ctx, self, days)
        if embed is None:
            return
        await ctx.send(embed=embed)

    @app_commands.command(name='forecast', description='Get the forecast for a location')
    @app_commands.describe(days='The amount of days in the future', location='The location')
    async def _forecast(self, interaction, days: int = 1, *, location: str):
        data = await self.http.forecast(location, days)

        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            await interaction.response.send_message(embed=error)
            return
        embed = await WeatherUtils.build_forecast_embed(data, interaction, self, days)

        if embed is None:
            return
        await interaction.response.send_message(embed=embed)

    @commands.command(aliases=['place', 'town'], description='Search a city.')
    async def city(self, ctx, index: Optional[int] = 1, *, query):
        data = await self.http.search(query)

        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            await ctx.send(embed=error)
            return
        embed = await WeatherUtils.build_search_embed(data, ctx, index)

        if embed is None:
            return
        await ctx.send(embed=embed)

    @app_commands.command(name='city', description='Search a city.')
    @app_commands.describe(query='The query')
    async def _city(self, interaction, index: int = 1, *, query: str):
        data = await self.http.search(query)

        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            await interaction.response.send_message(embed=error)
            return

        embed = await WeatherUtils.build_search_embed(data, interaction.response, index)
        if embed is None:
            return
        await interaction.response.send_message(embed=embed)

    @commands.command(aliases=['tz'], description='Get the timezone of a place.')
    async def timezone(self, ctx, *, location):
        data = await self.http.timezone(location)

        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            await ctx.send(embed=error)
            return

        embed = await WeatherUtils.build_tz_embed(data)
        await ctx.send(embed=embed)

    @app_commands.command(name='timezone', description='Get the timezone of a location')
    @app_commands.describe(location='The location')
    async def _timezone(self, interaction, location: str):
        data = await self.http.timezone(location)

        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            await interaction.response.send_message(embed=error)
            return

        embed = await WeatherUtils.build_tz_embed(data)
        await interaction.response.send_message(embed=embed)


async def setup(bot: MasterBot):
    await Weather.setup(bot)
