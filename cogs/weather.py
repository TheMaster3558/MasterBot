import discord
from discord.ext import commands, tasks
from cogs.utils.http import AsyncHTTPClient
from bot import MasterBot
import slash_util
from typing import Optional
import aiosqlite
from sqlite3 import IntegrityError
from datetime import datetime
import pytz
import time
import asyncio


class FlagUnits(commands.FlagConverter):
    speed: Optional[str] = None
    temp: Optional[str] = None


class WeatherAPIHTTPClient(AsyncHTTPClient):
    def __init__(self):
        super().__init__('http://api.weatherapi.com/v1/')
        self.api_key = '77aaea92eeeb4a1d80b41211220602'

    async def request(self, route, json=True, **params):
        return await super().request(route=route,
                                     json=json,
                                     key=self.api_key,
                                     **params)

    async def current(self, location):
        return await self.request('current.json', q=location, aqi='yes')


class Weather(slash_util.ApplicationCog):
    metric = {'temp': 'C', 'speed': 'kph'}
    customary = {'temp': 'F', 'speed': 'mph'}

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = WeatherAPIHTTPClient()
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
        embed = discord.Embed(title=f'{data.get("location").get("name")}, {data.get("location").get("region")}, {data.get("location").get("country")}',
                              timestamp=ctx.message.created_at)
        tz = pytz.timezone(data['location']['tz_id'])
        local_time = datetime.fromtimestamp(data['location']["localtime_epoch"], tz)
        local_time = local_time.strftime('%H:%M')
        embed.set_footer(text=f'Local Time: {local_time}')
        temp_unit = self.temp_units.get(ctx.guild.id) or 'C'
        speed_unit = self.speed_units.get(ctx.guild.id) or 'kph'
        data = data.get('current')
        if temp_unit == 'C':
            temp = data.get('temp_c')
            feels_like = data.get('feelslike_c')
        else:
            temp = data.get('temp_f')
            feels_like = data.get('feelslike_f')
        embed.add_field(name='Temperature', value=f'{temp} {temp_unit}')
        embed.add_field(name='Feels Like', value=f'{feels_like} {temp_unit}')
        embed.add_field(name='Weather', value=data.get('condition').get('text'))
        if speed_unit == 'kph':
            speed = data.get('wind_kph')
            visibility = str(data.get('vis_km')) + ' km'
        else:
            speed = data.get('wind_mph')
            visibility = str(data.get('vis_miles')) + ' miles'
        embed.add_field(name='Wind Direction', value=data.get('wind_dir'))
        embed.add_field(name='Wind Speed', value=f'{speed} {speed_unit}')
        embed.add_field(name='Visibility', value=visibility)
        last_updated_at = data.get('last_updated_epoch')
        last_updated_at = datetime.fromtimestamp(last_updated_at)
        last_updated_at = round(time.mktime(last_updated_at.timetuple()))
        embed.add_field(name='Last Updated At', value=f'<t:{last_updated_at}:R>')
        embed.set_thumbnail(url='https:' + data.get('condition').get('icon'))
        await ctx.send(embed=embed)


def setup(bot: MasterBot):
    bot.add_cog(Weather(bot))
