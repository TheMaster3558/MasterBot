# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from io import BytesIO

import discord
import matplotlib as mlt
import matplotlib.pyplot as plt
from discord.ext import commands

from cogs.utils.view import View

if TYPE_CHECKING:
    from cogs.f1 import Formula1


MISSING = discord.utils.MISSING


def humanize_time(millis: float, *_) -> str:
    millis = float(millis)
    time = ""

    hours = int(millis // 3600000)
    if hours > 0:
        time += f"{hours}"
    millis -= hours * 3600000

    minutes = int(millis // 60000)
    if minutes > 0:
        if time:
            time += ':'
        time += str(minutes)

    millis -= minutes * 60000

    seconds = int(millis // 1000)
    if seconds > 0:
        time += f":{seconds}"
    millis -= seconds // 1000

    if millis != 0:
        time += f".{str(int(millis))[-3:]}"

    return time


def time_to_millis(time: str) -> int:
    time = time.replace('.', ':')
    minutes, seconds, millis = time.split(':')

    total = (int(minutes) * 60000) + (int(seconds) * 1000) + int(millis)
    return total


class YearConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> int:
        if int(argument) >= 1950:
            return int(argument)
        raise commands.BadArgument("F1 did not exist back then.")


class CompareDriverSelect(discord.ui.Select):
    def __init__(self, drivers):
        driver_ids = {v: k for k, v in F1Utils.driver_ids.items()}

        options = [
            discord.SelectOption(label=name, value=driver_ids[name]) for name in drivers
        ]
        super().__init__(placeholder='Select a driver', options=options, min_values=1, max_values=20)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        self.disabled = True
        await interaction.edit_original_message(view=self.view)

        self.view.stop()


class DriverSelect(discord.ui.Select["DriverResultsView"]):
    def __init__(self, names: list[str]):
        options = [discord.SelectOption(label=name) for name in names]
        super().__init__(
            placeholder="Select a driver for more info",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            driver = self.values[0]
        except KeyError:
            driver = None

        await self.view.set(driver)


class DriverResultsView(View):
    def __init__(self, drivers: dict[str, discord.Embed], home: discord.Embed, *, author: discord.User, cog: Formula1,
                 lap_times: dict):
        super().__init__(timeout=600)
        self.cog = cog
        self.author = author

        self.home = home
        self.message: discord.Message = MISSING
        self.drivers = drivers

        self.current_driver: str | None = None
        self.current_embed: discord.Embed | None = None

        select = DriverSelect(list(drivers))
        self.add_item(select)

        self.lap_data = [lap['Timings'] for lap in lap_times]

    async def set(self, driver: str | None = None, embed: discord.Embed = None):
        embed = embed if embed else self.drivers.get(driver)

        self.current_driver = driver
        self.current_embed = embed

        if driver:
            for child in self.children:
                if child.label == 'Lap Times':  # type: ignore
                    child.disabled = False
                    break
        else:
            for child in self.children:
                if child.label == 'Compare':  # type: ignore
                    child.disabled = True

        await self.message.edit(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author

    @discord.ui.button(label='Home', style=discord.ButtonStyle.blurple)
    async def home(self, interaction, button):
        await interaction.response.defer()
        if self.current_embed is self.drivers.get(self.current_driver):
            await self.set(embed=self.home)
            return
        await self.set(self.current_driver)

    @discord.ui.button(label='Compare', style=discord.ButtonStyle.gray)
    async def compare(self, interaction, button):
        await interaction.response.defer()

        select = CompareDriverSelect(self.drivers)
        view = discord.ui.View().add_item(select)

        await interaction.followup.send(view=view, ephemeral=True)
        await view.wait()

        data = []
        drivers = []
        colors = []

        for driver in select.values:
            times = await F1Utils.process_lap_times(self.lap_data, driver)
            data.append(times)

            drivers.append(F1Utils.driver_ids[driver])

            color = F1Utils.team_colors.get(F1Utils.driver_teams.get(driver))
            color = discord.Color.from_rgb(*color) if isinstance(color, tuple) else discord.Color.random()
            colors.append(color)

        plot = await F1Utils.build_lap_times_plot(data, drivers, colors)
        await interaction.followup.send(file=plot)

    @discord.ui.button(label='Lap Times', style=discord.ButtonStyle.gray, disabled=True)
    async def lap_times(self, interaction, button):
        await interaction.response.defer()
        times = await F1Utils.process_lap_times(self.lap_data, self.current_driver)
        plot = await F1Utils.build_lap_times_plot([times], [self.current_driver], [self.current_embed.color])
        await interaction.followup.send(file=plot)


class F1Utils:
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)

    plot_lock = asyncio.Lock()

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

    driver_ids = {'max_verstappen': 'Max Verstappen', 'perez': 'Sergio Pérez', 'norris': 'Lando Norris', 'russell': 'George Russell', 'bottas': 'Valtteri Bottas', 'leclerc': 'Charles Leclerc', 'tsunoda': 'Yuki Tsunoda', 'vettel': 'Sebastian Vettel', 'kevin_magnussen': 'Kevin Magnussen', 'stroll': 'Lance Stroll', 'albon': 'Alexander Albon', 'gasly': 'Pierre Gasly', 'hamilton': 'Lewis Hamilton', 'ocon': 'Esteban Ocon', 'zhou': 'Guanyu Zhou', 'latifi': 'Nicholas Latifi', 'mick_schumacher': 'Mick Schumacher', 'ricciardo': 'Daniel Ricciardo', 'alonso': 'Fernando Alonso', 'sainz': 'Carlos Sainz'}

    driver_teams = {
        'max_verstappen': 'red_bull',
        'perez': 'red_bull',
        'norris': 'mclaren',
        'russell': 'mercedes',
        'bottas': 'alfa',
        'lecerlc': 'ferrari',
        'tsunoda': 'alphatauri',
        'vettel': 'aston_martin',
        'kevin_magnussen': 'haas',
        'stroll': 'aston_martin',
        'albon': 'williams',
        'gasly': 'alphatauri',
        'hamilton': 'mercedes',
        'ocon': 'alphine',
        'zhou': 'alfa',
        'latifi': 'williams',
        'ricciardo': 'mclaren',
        'mich_schumacher': 'haas',
        'alonso': 'alpine',
        'sainz': 'ferrari'
    }

    @classmethod
    def get_color(cls, constructor: dict) -> discord.Color | None:
        return (
            discord.Color.from_rgb(*(cls.team_colors[constructor["constructorId"]]))
            or None
        )

    @classmethod
    async def build_qualifying_embeds(cls, data) -> list[discord.Embed]:
        race_name = data["raceName"]
        results: list = data["QualifyingResults"]

        embeds = []
        for driver in results:
            constructor = driver.get("Constructor", {})

            color = cls.get_color(constructor)

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

        return embeds

    @classmethod
    async def build_teams_embed(cls, data) -> list[discord.Embed]:
        embeds = []
        for team in data:
            color = cls.get_color(team)

            embed = discord.Embed(title=team["name"], url=team["url"], color=color)
            embed.add_field(name="Nationality", value=team["nationality"])
            embeds.append(embed)

        return embeds

    @classmethod
    async def build_constructors_standings_embed(cls, data) -> discord.Embed:
        lines = []
        color = cls.get_color(data[0]["Constructor"])

        for team in data:
            name = team["Constructor"]["name"]
            position = team["position"]
            points = team["points"]
            wins = team["wins"]
            line = f"{position}. {name} | {points} points | {wins} wins"
            lines.append(line)

        embed = discord.Embed(
            title="Constructors Standings", color=color, description="\n".join(lines)
        )
        return embed

    @classmethod
    async def build_drivers_standings_embed(cls, data) -> discord.Embed:
        lines = []
        color = cls.get_color(data[0]["Constructor"])

        for driver in data:
            name = f"{driver['Driver']['givenName']} {driver['Driver']['familyName']}"
            position = driver["position"]
            points = driver["points"]
            wins = driver["wins"]
            line = f"{position}. {name} | {points} points | {wins} wins"
            lines.append(line)

        embed = discord.Embed(
            title="Drivers Standings", color=color, description="\n".join(lines)
        )
        return embed

    @staticmethod
    async def build_schedule_embed(data) -> list[discord.Embed]:
        embeds = []

        for race in data:
            embed = discord.Embed(title=race["raceName"], url=race["url"])
            embed.add_field(name="Circuit", value=race["Circuit"]["circuitName"])

            locality = race["Circuit"]["Location"]["locality"]
            country = race["Circuit"]["Location"]["country"]
            embed.add_field(name="Location", value=f"{locality}, {country}")
            embed.add_field(name="Data", value=race["date"])

            embeds.append(embed)

        return embeds

    @classmethod
    async def build_race_result_main_embed(cls, data, image=None) -> discord.Embed:
        results = data["Results"]
        color = cls.get_color(results[0]["Constructor"])

        embed = discord.Embed(title=f"{data['raceName']} {data['season']}", color=color)

        podium = []
        dnf = []
        fastest_lap = None
        for driver in results:
            text = f"{driver['position']}. {driver['Driver']['code']} | Grid: {driver['grid']}"
            if int(driver["position"]) <= 3:
                podium.append(text)
            if driver["status"] != "Finished" and not driver["status"].startswith("+"):
                text += f" | {driver['laps']} laps ({driver['status']})"
                dnf.append(text)
            try:
                if driver["FastestLap"]["rank"] == "1":
                    fastest_lap = f"{driver['Driver']['code']} {driver['FastestLap']['Time']['time']}"
            except KeyError:
                pass

        embed.add_field(name="Podium", value="\n".join(podium))
        embed.add_field(name="DNF", value="\n".join(dnf))
        embed.add_field(name="Fastest Lap", value=fastest_lap)

        if image:
            embed.set_thumbnail(url=image)

        return embed

    @classmethod
    async def build_driver_results_embed(cls, data) -> dict[str, discord.Embed]:
        embeds = {}

        for driver in data["Results"]:
            color = cls.get_color(driver["Constructor"])
            name = f"{driver['Driver']['givenName']} {driver['Driver']['familyName']}"

            embed = discord.Embed(title=f"{data['raceName']} | {name}", color=color)

            embed.add_field(name="Final Position", value=driver["position"])
            embed.add_field(name="Grid Position", value=driver["grid"])
            embed.add_field(name="Points", value=driver["points"])
            embed.add_field(name="Laps Completed", value=driver["laps"])
            embed.add_field(name="Status", value=driver["status"])
            try:
                time = humanize_time(driver["Time"]["millis"])
                embed.add_field(name="Time Taken", value=time)
            except KeyError:
                pass

            try:
                embed.add_field(
                    name="Fastest Lap", value=driver["FastestLap"]["Time"]["time"]
                )
            except KeyError:
                pass
            embeds[name] = embed
        return embeds

    @classmethod
    async def process_lap_times(cls, lap_data, driver) -> list[int]:
        data = []
        for lap in lap_data:
            for d in lap:
                try:
                    if driver in (cls.driver_ids[d['driverId']], d['driverId']):
                        data.append(d['time'])
                except KeyError:
                    pass

        return [time_to_millis(time) for time in data]

    @classmethod
    async def build_lap_times_plot(cls, data: list[list[int]], drivers, colors: list) -> discord.File:
        def blocking_build() -> discord.File:
            fig, ax = plt.subplots()
            ax.yaxis.set_major_formatter(mlt.ticker.FuncFormatter(humanize_time))

            for i, d in enumerate(data):
                x = [i for i in range(1, len(d) + 1)]
                y = d
                y.extend(0 for _ in range(len(x) - len(y)))  # in case of DNF

                ax.plot(x, y, label=drivers[i], color=str(colors[i]))

            plt.xlabel('Lap')
            plt.ylabel('Time')
            plt.title('Driver Lap Times')
            plt.legend()

            with BytesIO() as image_binary:
                fig.savefig(image_binary, format='png')
                image_binary.seek(0)
                file = discord.File(image_binary, 'lap_times.png')
            return file

        async with cls.plot_lock:
            return await asyncio.to_thread(blocking_build)
