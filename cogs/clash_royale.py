from functools import lru_cache
from typing import Optional
from requests.structures import CaseInsensitiveDict

import discord
from discord import app_commands
from discord.ext import commands

from cogs.utils.http import AsyncHTTPClient
from cogs.utils.cr_utils import ClashRoyaleUtils
from bot import MasterBot
from static_embeds import cr_locations_embed, locations
from cogs.utils.app_and_cogs import Cog, QuickObject


class CountryError(Exception):
    """
    Exception to deal with bad countries that the user gives.
    """

    pass


class ClashRoyaleHTTPClient(AsyncHTTPClient):
    def __init__(self, api_key, loop):
        self.api_key = api_key
        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Bearer {api_key}"
        headers["content-type"] = "application/json"
        super().__init__("https://api.clashroyale.com/v1/", headers=headers, loop=loop)

    async def player_request(self, tag) -> dict:
        """
        :param tag: the player tag
        :return: dict
        """
        return await self.request(f"players/%23{tag}")

    async def battle_log(self, tag):
        """
        :param tag: the players tag
        """
        return await self.request(f"players/%23{tag}/battlelog")

    @lru_cache(maxsize=110)
    async def cards_request(self, **params) -> list:
        """
        :param params: limit, before, after
        :return: list
        """
        resp = await self.request("cards", **params)
        return resp.get("items")

    async def clans_request(self, limit=5, **params) -> list:
        """
        :param limit: the amount of clans to return
        :param params:
        :return: list
        """
        copy = {k: v for k, v in params.items() if v}
        resp = await self.request("clans", **copy, limit=limit)
        clans = (clan for clan in resp.get("items"))
        return [await self.clan_tag_request(clan.get("tag")[1:]) for clan in clans]

    async def clan_tag_request(self, tag):
        return await self.request(f"clans/%23{tag}")


class ClanSearchFlags(commands.FlagConverter):
    name: Optional[str]
    location: Optional[str | int]
    min: Optional[int]
    max: Optional[int]
    score: Optional[int]
    result: Optional[int] = 1


class ClashRoyale(Cog, name="clashroyale"):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.api_key = self.bot.clash_royale
        self.http = ClashRoyaleHTTPClient(self.api_key, loop=self.bot.loop)
        print("Clash Royale cog loaded")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Try again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, commands.CommandInvokeError) and isinstance(
            error.original, AttributeError
        ):
            await ctx.send("I couldn't find that tag.")
        else:
            await self.bot.on_command_error(ctx, error)

    @commands.hybrid_command(
        description="Get a list of locations to use for clash royale commands."
    )
    async def crlocations(self, ctx):
        await ctx.author.send(embed=cr_locations_embed)

        if ctx.interaction:
            await ctx.interaction.response.send_message(
                "Check your DMs", ephemeral=True
            )

    @commands.hybrid_command(description="Get the stats of a clash royale player.")
    @app_commands.describe(player_tag="The players tag")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def stats(self, ctx: commands.Context, *, player_tag: str):
        await ctx.typing()
        if player_tag.startswith("#"):
            player_tag = player_tag[1:]

        data = await self.http.player_request(player_tag)
        embed = await ClashRoyaleUtils.build_player_embed(data)
        await ctx.send(embed=embed)

    @stats.error
    async def error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Try giving me a real tag.")
            await self.bot.on_command_error(ctx, error)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"Wait a bit. Try in {round(error.retry_after)}", ephemeral=True
            )
        else:
            await self.bot.on_command_error(ctx, error)

    @commands.hybrid_command(description="Get a clash royale card.")
    @app_commands.describe(name="The card name")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def card(self, ctx: commands.Context, *, name: str):
        await ctx.typing()
        cards = await self.http.cards_request()

        card = ClashRoyaleUtils.search_for_card(cards, name)
        embed = await ClashRoyaleUtils.build_card_embed(card)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Get clash royale clan stats.")
    @app_commands.describe(clan_tag="The clan tag")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def clan(self, ctx: commands.Context, clan_tag: str):
        await ctx.typing()
        if clan_tag.startswith("#"):
            clan_tag = clan_tag[1:]

        clan = await self.http.clan_tag_request(clan_tag)
        embed = await ClashRoyaleUtils.build_clan_embed(clan)
        await ctx.send(embed=embed)

    @commands.command(name="searchclan", description="Search up a clan in clash royale")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def search_clan(self, ctx: commands.Context, *, flags):
        await ctx.typing()

        flags = await ClanSearchFlags().convert(ctx, flags)
        if isinstance(flags.location, str):
            flags.location = locations.get(flags.location.lower())
            if flags.location is None:
                raise CountryError()
        elif isinstance(flags.location, int):
            pass

        clans = await self.http.clans_request(
            name=flags.name,
            locationId=flags.location,
            minMembers=flags.min,
            maxMembers=flags.max,
            minScore=flags.score,
        )

        try:
            clan = clans[flags.result - 1]
        except IndexError:
            return await ctx.send("Not enough clans were found.")
        await self.clan(ctx, clan.get("tag"))

    @search_clan.error
    async def error(self, ctx, error):
        if isinstance(
            error,
            (
                commands.MissingRequiredArgument,
                commands.MissingFlagArgument,
                commands.MissingRequiredFlag,
            ),
        ):
            embed = discord.Embed(title="You missed a flag argument dummy.")
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, TypeError):
                await ctx.send("I couldn't find that clan.")
                return
            embed = discord.Embed(
                title="Invalid Country",
                description=f"You may have a bad country. Use `{self.bot.command_prefix(self.bot, ctx.message)[2]}crlocations` for a list. ",
            )
            await ctx.send(embed=embed)
            await self.bot.on_command_error(ctx, error)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Wait a bit. Try in {round(error.retry_after)} seconds.")
        else:
            await self.bot.on_command_error(ctx, error)

    @app_commands.command(
        name="searchclan", description="Search up a clan in clash royale."
    )
    @app_commands.describe(
        name="The clans name",
        location="The clan location",
        min="The minimum amount of members",
        max="The maximum amount of members",
        score="The minimum clan score",
        result="The result to give back",
    )
    async def _search_clan(
        self,
        interaction,
        name: str = "",
        location: str = "",
        min: int = 0,
        max: int = 50,
        score: int = 0,
        result: app_commands.Range[int, 1, 10] = 1,
    ):
        ctx = await commands.Context.from_interaction(interaction)
        flags = QuickObject(
            name=name, location=location, min=min, max=max, score=score, result=result
        )
        await self.search_clan(ctx, flags=flags)


async def setup(bot: MasterBot):
    await ClashRoyale.setup(bot)
