import discord
from discord.ext import commands

from cogs.utils.app_and_cogs import Cog
from cogs.utils.http import AsyncHTTPClient
from cogs.utils.view import Paginator
from bot import MasterBot
from cogs.utils.f1_utils import F1Utils


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


class Formula1(Cog, name="formula one"):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = ErgastHTTPClient(self.bot.loop)
        print("Formula One cog loaded")

    @commands.command()
    async def qualifying(self, ctx, year: int = 2022, race: int = 3):
        data = await self.http.qualifying_results(year, race)
        embeds = await F1Utils.build_qualifying_embeds(data)

        view = Paginator(embeds)
        await view.send(ctx.channel)

    @commands.command()
    async def constructors(self, ctx, year: int = 2022):
        data = await self.http.constructors(year)
        embeds = await F1Utils.build_teams_embed(data["Constructors"])

        view = Paginator(embeds)
        await view.send(ctx.channel)

    @commands.group()
    async def standings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @standings.command()
    async def constructors(self, ctx, year: int = 2022, race: int = None):
        data = await self.http.constructors_standings(year, race)
        embed = await F1Utils.build_constructors_standings_embed(data)

        await ctx.send(embed=embed)


async def setup(bot: MasterBot):
    await Formula1.setup(bot)
