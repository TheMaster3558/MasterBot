import discord
from discord.ext import commands, tasks
from masterbot.cogs.utils.http import AsyncHTTPClient
from masterbot.bot import MasterBot
import slash_util
from typing import Optional
import aiosqlite
from sqlite3 import IntegrityError
import asyncio
from masterbot.cogs.utils.weather_utils import WeatherUtils


class FlagUnits(commands.FlagConverter):
    speed: Optional[str] = None
    temp: Optional[str] = None


class WeatherAPIHTTPClient(AsyncHTTPClient):
    def __init__(self, api_key):
        super().__init__('http://api.weatherapi.com/v1/')
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


class Weather(slash_util.Cog):
    metric = {'temp': 'C', 'speed': 'kph'}
    customary = {'temp': 'F', 'speed': 'mph'}

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = WeatherAPIHTTPClient(self.bot.api_keys.weather)
        self.temp_units = {}
        self.speed_units = {}
        self.db = None
        self.update_db.start()
        print('Weather cog loaded')

    async def fetch_units(self):
        for guild in self.bot.guilds:
            cursor = await self.db.execute(f"""SELECT temp, speed FROM units
                                        WHERE id = {guild.id};""")
            data = await cursor.fetchone()
            if data is None:
                continue
            temp, speed = data
            self.temp_units[guild.id] = temp
            self.speed_units[guild.id] = speed

    @tasks.loop(seconds=5)
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
        await asyncio.sleep(1)
        await self.update_db()

    @commands.command()
    async def units(self, ctx, *, flags: FlagUnits):
        if not flags.temp and not flags.speed:
            return await ctx.send(f'You forgot the flag arguments. `{ctx.prefix}units <flags_args>`. **Args:**\n`temp` `C` or `F`\n`speed` `mph` or `kph``')
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
        await ctx.send(f'New settings! Temp: `{self.temp_units[ctx.guild.id]}` Speed: `{self.speed_units[ctx.guild.id]}`')

    @commands.command()
    async def current(self, ctx, *, location):
        data = await self.http.current(location)
        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            return await ctx.send(embed=error)
        embed = await WeatherUtils.build_current_embed(data, ctx, self)
        if embed is None:
            return
        await ctx.send(embed=embed)

    @commands.command()
    async def forecast(self, ctx, days: Optional[int] = 1, *, location):
        data = await self.http.forecast(location, days)
        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            return await ctx.send(embed=error)
        embed = await WeatherUtils.build_forecast_embed(data, ctx, self, days)
        if embed is None:
            return
        await ctx.send(embed=embed)

    @commands.command(aliases=['place', 'town'])
    async def city(self, ctx, index: Optional[int] = 1, *, query):
        data = await self.http.search(query)
        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            return await ctx.send(embed=error)
        embed = await WeatherUtils.build_search_embed(data, ctx, index, ctx.message.created_at)
        if embed is None:
            return
        await ctx.send(embed=embed)

    @commands.command(aliases=['tz'])
    async def timezone(self, ctx, *, location):
        data = await self.http.timezone(location)
        if data.get('error'):
            error = discord.Embed(title='Error',
                                  description=data.get('error').get('message'))
            return await ctx.send(embed=error)
        embed = await WeatherUtils.build_tz_embed(data)
        await ctx.send(embed=embed)


def setup(bot: MasterBot):
    bot.add_cog(Weather(bot))
