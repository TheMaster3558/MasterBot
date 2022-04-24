from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from cogs.utils.app_and_cogs import Cog
from cogs.utils.http import AsyncHTTPClient
from cogs.utils.view import Paginator
from bot import MasterBot
from cogs.utils.f1_utils import F1Utils, YearConverter


class ErgastHTTPClient(AsyncHTTPClient):
    def __init__(self, loop):
        super().__init__("http://ergast.com/api/f1", loop=loop, suffix=".json")

    async def qualifying_results(self, year, race):
        data: dict = (await self.request(f"/{year}/{race}/qualifying"))["MRData"][
            "RaceTable"
        ]
        return data["Races"][0]

    async def constructors(self, year: int | None = None):
        url = ""
        if year:
            url += f"/{year}"
        url += "/constructors"
        return (await self.request(url))["MRData"]["ConstructorTable"]

    async def constructors_standings(
        self, year: int | None = None, race: int | None = None
    ):
        url = f"/{year or 'current'}"
        if race:
            url += f"/{race}"
        return (await self.request(f"{url}/constructorStandings"))["MRData"][
            "StandingsTable"
        ]["StandingsLists"][0]["ConstructorStandings"]

    async def drivers_standings(self, year: int | None = None, race: int | None = None):
        url = f"/{year or 'current'}"
        if race:
            url += f"/{race}"
        return (await self.request(f"{url}/driverStandings"))["MRData"][
            "StandingsTable"
        ]["StandingsLists"][0]["DriverStandings"]

    async def schedule(self, year: int | None = None):
        year = year or "current"
        return (await self.request(str(year)))["MRdata"]


class Formula1(Cog, name="formula one"):
    current_year = 2022
    current_race = 4

    year_param = commands.parameter(converter=YearConverter, default=current_year)

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = ErgastHTTPClient(self.bot.loop)
        print("Formula One cog loaded")

    @commands.hybrid_command(description="Get the qualifying results.")
    @app_commands.describe(
        year="The year of the season", race="The race in the reason."
    )
    async def qualifying(
        self, ctx, year: Optional[YearConverter] = None, race: int = current_race
    ):
        year = year or self.current_year

        data = await self.http.qualifying_results(year, race)
        embeds = await F1Utils.build_qualifying_embeds(data)

        view = Paginator(embeds)
        await view.send(ctx)

    @commands.hybrid_group(description="Get the standings.")
    async def standings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @standings.command(description="Constructors standings")
    @app_commands.describe(
        year="The year of the season", race="The race in the reason."
    )
    async def constructors(
        self, ctx, year: Optional[YearConverter] = None, race: int = current_race
    ):
        data = await self.http.constructors_standings(year, race)
        embed = await F1Utils.build_constructors_standings_embed(data)

        await ctx.send(embed=embed)

    @standings.command(description="Drivers standings")
    @app_commands.describe(
        year="The year of the season", race="The race in the reason."
    )
    async def drivers(
        self, ctx, year: Optional[YearConverter] = None, race: int = current_race
    ):
        data = await self.http.drivers_standings(year, race)
        embed = await F1Utils.build_drivers_standings_embed(data)

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def schedule(self, ctx, year: YearConverter = None):
        data = await self.http.schedule(year)


async def setup(bot: MasterBot):
    await Formula1.setup(bot)
