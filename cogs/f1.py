from typing import Optional

import discord
from discord.ext import commands

from cogs.utils.app_and_cogs import Cog
from cogs.utils.http import AsyncHTTPClient
from cogs.utils.view import Paginator
from bot import MasterBot


team_colors: dict[str, tuple[int, int, int]] = {
    "ferrari": (237, 28, 36),
    "red_bull": (30, 91, 198),
    "mercedes": (108, 211, 191),
    "mclaren": (245, 128, 32),
    "alpine": (34, 147, 209),
    "alfa": (172, 32, 57),
    "alphatauri": (78, 124, 155),
    "haas": (182, 186, 189),
    "williams": (55, 190, 221),
    "aston_martin": (45, 130, 109),
}


class ErgastHTTPClient(AsyncHTTPClient):
    def __init__(self, loop):
        super().__init__("http://ergast.com/api/f1", loop=loop, suffix=".json")

    async def qualifying_results(self, year, race):
        data: dict = (await self.request(f"/{year}/{race}/qualifying"))["MRData"][
            "RaceTable"
        ]
        return data["Races"][0]


class Formula1(Cog, name="formula one"):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = ErgastHTTPClient(self.bot.loop)
        print("Formula One cog loaded")

    @commands.command()
    async def qualifying(self, ctx, year: Optional[int] = 2022, race: int = 3):
        data = await self.http.qualifying_results(year, race)
        race_name = data["raceName"]
        results: list = data["QualifyingResults"]

        embeds = []
        for driver in results:
            constructor = driver.get("Constructor", {})

            color = (
                discord.Color.from_rgb(*(team_colors[constructor["constructorId"]]))
                or None
            )

            embed = discord.Embed(title=f"{race_name} Qualifying", color=color)
            driver_name = (
                f"{driver['Driver']['givenName']} {driver['Driver']['familyName']}"
            )
            embed.add_field(name="Driver", value=driver_name)
            embed.add_field(name="Position", value=results.index(driver) + 1)
            embed.add_field(name="Team", value=constructor.get("name", "No team"))

            embed.add_field(name="Q1", value=driver.get("Q1") or "None")
            embed.add_field(name="Q2", value=driver.get("Q2") or "None")
            embed.add_field(name="Q3", value=driver.get("Q3") or "None")

            embeds.append(embed)

        view = Paginator(embeds)
        msg = await ctx.send(view=view, embed=embeds[0])
        view.configure_message(msg)

        await view.wait()
        await view.disable_all(msg)


async def setup(bot: MasterBot):
    await Formula1.setup(bot)
