import discord
from discord.ext import commands

from cogs.utils.view import View


MISSING = discord.utils.MISSING


def humanize_time(millis: float) -> str:
    millis = float(millis)
    time = ""

    hours = int(millis // 3600000)
    if hours > 0:
        time += f"{hours}"
    millis -= hours * 3600000

    minutes = int(millis // 60000)
    if minutes > 0:
        time += f":{minutes}"
    millis -= minutes * 60000

    seconds = int(millis // 1000)
    if seconds > 0:
        time += f":{seconds}"
    millis -= seconds // 1000

    time += f".{str(int(millis))[-3:]}"

    return time


class YearConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> int:
        if int(argument) >= 1950:
            return int(argument)
        raise commands.BadArgument("F1 did not exist back then.")


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
        self.view.message = interaction.message
        await self.view.edit_message(self.values[0])


class DriverResultsView(View):
    def __init__(self, drivers: dict[str, discord.Embed], home: discord.Embed):
        super().__init__(timeout=600)

        self.message: discord.Message = MISSING
        self.drivers = drivers
        self.home = home

        select = DriverSelect(list(drivers.keys()))
        self.add_item(select)

    async def edit_message(self, driver: str = None, embed: discord.Embed = None):
        embed = embed if embed is not None else self.drivers.get(driver)
        await self.message.edit(embed=embed)

    @discord.ui.button(label="Home", style=discord.ButtonStyle.blurple)
    async def home(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.edit_message(embed=self.home)
        await interaction.response.defer()


class F1Utils:
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
                embed.add_field(name="Time Taken", value=time, inline=False)
            except KeyError:
                pass

            try:
                embed.add_field(
                    name="Fastest Lap", value=driver["FastestLap"]["Time"]["time"]
                )
            except KeyError:
                pass
            try:
                embed.add_field(
                    name="Average Speed",
                    value=f"{driver['AverageSpeed']['speed']} {driver['AverageSpeed']['units']}",
                )
            except KeyError:
                pass
            print(driver.keys())
            embeds[name] = embed

        return embeds
