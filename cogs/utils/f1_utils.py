import discord
from discord.ext import commands


class YearConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> int:
        if int(argument) >= 1950:
            return int(argument)
        raise commands.BadArgument("F1 did not exist back then.")


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
    async def build_qualifying_embeds(cls, data) -> list[discord.Embed]:
        race_name = data["raceName"]
        results: list = data["QualifyingResults"]

        embeds = []
        for driver in results:
            constructor = driver.get("Constructor", {})

            color = (
                discord.Color.from_rgb(*(cls.team_colors[constructor["constructorId"]]))
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

        return embeds

    @classmethod
    async def build_teams_embed(cls, data) -> list[discord.Embed]:
        embeds = []
        for team in data:
            if (team_id := team["constructorId"]) in cls.team_colors:
                color = discord.Color.from_rgb(*(cls.team_colors[team_id]))
            else:
                color = None

            embed = discord.Embed(title=team["name"], url=team["url"], color=color)
            embed.add_field(name="Nationality", value=team["nationality"])
            embeds.append(embed)

        return embeds

    @classmethod
    async def build_constructors_standings_embed(cls, data) -> discord.Embed:
        lines = []
        color = discord.Color.from_rgb(
            *(cls.team_colors[data[0]["Constructor"]["constructorId"]])
        )

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
        color = discord.Color.from_rgb(
            *(cls.team_colors[data[0]["Constructors"][0]["constructorId"]])
        )

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
        print(data)
