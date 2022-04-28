from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from cogs.utils.app_and_cogs import Cog
from cogs.utils.http import AsyncHTTPClient
from cogs.utils.view import Paginator
from bot import MasterBot
from cogs.utils.f1_utils import F1Utils, DriverResultsView


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
        return (await self.request(f"/{year}"))["MRData"]["RaceTable"]["Races"]

    async def race_results(self, year: int | None = None, race: int | None = None):
        year, race = year or "current", race or "current"
        return (await self.request(f"/{year}/{race}/results"))["MRData"]["RaceTable"][
            "Races"
        ][0]


class Formula1(Cog, name="formula one"):
    current_year = 2022
    current_race = 4
    current_image = (
        "https://th.bing.com/th/id/OIF.CZKE3ftwq7y1L52CTwPkkg?pid=ImgDet&rs=1"
    )

    year_param = commands.Range[int, 1950, current_year]

    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = ErgastHTTPClient(self.bot.loop)
        print("Formula One cog loaded")

    async def cog_command_error(self, ctx, error) -> None:
        if isinstance(error, commands.RangeError):
            await ctx.send(str(error))
        elif isinstance(error, commands.CommandInvokeError) and isinstance(
            error.original, IndexError
        ):
            await ctx.send("That race was not found.")

    @commands.hybrid_command(description="Get the qualifying results.")
    @app_commands.describe(
        year="The year of the season", race="The race in the reason."
    )
    async def qualifying(
        self, ctx, year: Optional[year_param] = None, race: int = current_race
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

    @standings.command(description="The constructors standings")
    @app_commands.describe(
        year="The year of the season", race="The race in the reason."
    )
    async def constructors(
        self, ctx, year: Optional[year_param] = None, race: int = current_race
    ):
        data = await self.http.constructors_standings(year, race)
        embed = await F1Utils.build_constructors_standings_embed(data)

        await ctx.send(embed=embed)

    @standings.command(description="The drivers standings")
    @app_commands.describe(
        year="The year of the season", race="The race in the reason."
    )
    async def drivers(
        self, ctx, year: Optional[year_param] = None, race: int = current_race
    ):
        data = await self.http.drivers_standings(year, race)
        embed = await F1Utils.build_drivers_standings_embed(data)

        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Get schedule of a f1 season")
    @app_commands.describe(year="The year of the season")
    async def schedule(self, ctx, year: year_param = None):
        data = await self.http.schedule(year)
        embeds = await F1Utils.build_schedule_embed(data)

        view = Paginator(embeds, starting_page=self.current_race - 1)
        await view.send(ctx)

    @commands.hybrid_command(description="Get the results of a race")
    async def results(self, ctx, year: year_param = None, race: int = current_race):
        data = await self.http.race_results(year, race)

        embed = await F1Utils.build_race_result_main_embed(data, self.current_image)
        drivers = await F1Utils.build_driver_results_embed(data)

        view = DriverResultsView(drivers, embed)
        await ctx.send(embed=embed, view=view)


async def setup(bot: MasterBot):
    await Formula1.setup(bot)
