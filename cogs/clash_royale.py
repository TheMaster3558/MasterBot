import discord
from discord.ext import commands
import slash_util
from typing import Optional, Union
from cogs.utils.http import AsyncHTTPClient
from requests.structures import CaseInsensitiveDict
from cogs.utils.cr_utils import ClashRoyaleUtils
from bot import MasterBot
from cogs.utils.help_utils import HelpSingleton
from static_embeds import cr_locations_embed, locations


class Help(metaclass=HelpSingleton):
    def __init__(self, prefix):
        self.prefix = prefix

    def crlocations_help(self):
        message = f'`{self.prefix}crlocations`: Get a list of locations to use for other commands.'
        return message

    def stats_help(self):
        message = f'`{self.prefix}stats <player_tag>`: Get clash royale player stats.'
        return message

    def clan_help(self):
        message = f'`{self.prefix}clan <clan_tag>`: Get clash royale clan stats.'
        return message

    def card_help(self):
        message = f'`{self.prefix}card <name>`: Get a clash royale card.'
        return message

    def search_clan_help(self):
        message = f'`{self.prefix}searchclan [flag_args]`:\n**Args for searchclan:**\n\t`name`: The name\n\t`location`: The location\n\t`min`: Minimum members\n\t`max`: Maximum members\n\t`score`: Minimum clan score\n\t`result`: Which result to choose. Defaults to first.'
        return message

    def full_help(self):
        help_list = [self.crlocations_help(), self.stats_help(), self.clan_help(), self.card_help(), self.search_clan_help()]
        return '\n'.join(help_list)


class CountryError(Exception):
    """
    Exception to deal with bad countries that the user gives.
    """
    pass


class ClashRoyaleHTTPClient(AsyncHTTPClient):
    def __init__(self, api_key, loop):
        self.api_key = api_key
        headers = CaseInsensitiveDict()
        headers['Authorization'] = f'Bearer {api_key}'
        headers['content-type'] = 'application/json'
        super().__init__('https://api.clashroyale.com/v1/', headers=headers, loop=loop)

    async def player_request(self, tag) -> dict:
        """
        :param tag: the player tag
        :return: dict
        """
        return await self.request(f'players/%23{tag}')

    async def battle_log(self, tag):
        """
        :param tag: the players tag
        """
        return await self.request(f'players/%23{tag}/battlelog')

    async def cards_request(self, **params) -> list:
        """
        :param params: limit, before, after
        :return: list
        """
        resp = await self.request('cards', **params)
        return resp.get('items')

    async def clans_request(self, limit=5, **params) -> list:
        """
        :param limit: the amount of clans to return
        :param params:
        :return: list
        """
        copy = {k: v for k, v in params.items() if v is not None}
        resp = await self.request('clans', **copy, limit=limit)
        clans = (clan for clan in resp.get('items'))
        return [await self.clan_tag_request(clan.get('tag')[1:]) for clan in clans]

    async def clan_tag_request(self, tag):
        return await self.request(f'clans/%23{tag}')


class ClanSearchFlags(commands.FlagConverter):
    name: Optional[str]
    location: Optional[Union[str, int]]
    min: Optional[int]
    max: Optional[int]
    score: Optional[int]
    result: Optional[int] = 1


class ClashRoyale(slash_util.Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.api_key = self.bot.clash_royale
        self.http = ClashRoyaleHTTPClient(self.api_key, self.bot.loop)
        print('Clash Royale cog loaded')

    @commands.command()
    async def crlocations(self, ctx):
        await ctx.author.send(embed=cr_locations_embed)

    @slash_util.slash_command(name='crlocations', description='Get a list of locations to use.')
    async def _crlocations(self, ctx):
        await self.crlocations(ctx)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def stats(self, ctx: commands.Context, *, player_tag: str):
        await ctx.trigger_typing()
        if player_tag.startswith('#'):
            player_tag = player_tag[1:]
        data = await self.http.player_request(player_tag)
        embed = await ClashRoyaleUtils.build_player_embed(data)
        await ctx.send(embed=embed)

    @stats.error
    async def error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send('Try giving me a real tag.')
            raise error
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Wait a bit. Try in {round(error.retry_after)}')
        else:
            raise error

    @slash_util.slash_command(name='stats', description='Get clash royale player stats.')
    @slash_util.describe(tag='The player tag')
    async def _stats(self, ctx, tag: str):
        if tag.startswith('#'):
            tag = tag[1:]
        data = await self.http.player_request(tag)
        embed = await ClashRoyaleUtils.build_player_embed(data)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def card(self, ctx: commands.Context, *, name: str):
        await ctx.trigger_typing()
        cards = await self.http.cards_request()
        card = ClashRoyaleUtils.search_for_card(cards, name)
        embed = await ClashRoyaleUtils.build_card_embed(card)
        await ctx.send(embed=embed)

    @card.error
    async def error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Wait a bit. Try in {round(error.retry_after)} seconds.')
        else:
            raise error

    @slash_util.slash_command(name='card', description='Get a clash royale card.')
    @slash_util.describe(name='The card name')
    async def _card(self, ctx, name: str):
        cards = await self.http.cards_request()
        try:
            card = ClashRoyaleUtils.search_for_card(cards, name)
        except ValueError as exc:
            return await ctx.send(exc, ephemeral=True)
        embed = await ClashRoyaleUtils.build_card_embed(card)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType)
    async def clan(self, ctx: commands.Context, tag: str):
        await ctx.trigger_typing()
        if tag.startswith('#'):
            tag = tag[1:]
        clan = await self.http.clan_tag_request(tag)
        embed = await ClashRoyaleUtils.build_clan_embed(clan)
        await ctx.send(embed=embed)

    @clan.error
    async def error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send('Try giving me a real tag.')
            raise error
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Calm down! Try in {error.retry_after} seconds.')
        else:
            raise error

    @slash_util.slash_command(name='clan', desription='Get clash royale clan stats')
    @slash_util.describe(tag='The clan tag')
    async def _clan(self, ctx, tag: str):
        if tag.startswith('#'):
            tag = tag[1:]
        clan = await self.http.clan_tag_request(tag)

        embed = await ClashRoyaleUtils.build_clan_embed(clan)
        await ctx.send(embed=embed)

    @commands.command(name='searchclan')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def search_clan(self, ctx: commands.Context, *, flags):
        await ctx.trigger_typing()
        flags = await ClanSearchFlags().convert(ctx, flags)
        if isinstance(flags.location, str):
            flags.location = locations.get(flags.location.lower())
            if flags.location is None:
                raise CountryError()
        elif isinstance(flags.location, int):
            pass
        clans = await self.http.clans_request(name=flags.name,
                                              locationId=flags.location,
                                              minMembers=flags.min,
                                              maxMembers=flags.max,
                                              minScore=flags.score)
        try:
            clan = clans[flags.result - 1]
        except IndexError:
            return await ctx.send('Not enough clans were found.')
        await self.clan(ctx, clan.get('tag'))

    @search_clan.error
    async def error(self, ctx, error):
        if isinstance(error, (commands.MissingRequiredArgument, commands.MissingFlagArgument, commands.MissingRequiredFlag)):
            embed = discord.Embed(title='You missed a flag argument dummy.')
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, TypeError):
                return await ctx.send("I couldn't find that clan.")
            embed = discord.Embed(title='Invalid Country',
                                  description=f'You may have a bad country. Use `{self.bot.command_prefix(self.bot, ctx.message)[2]}crlocations` for a list. ')
            await ctx.send(embed=embed)
            raise error
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Wait a bit. Try in {round(error.retry_after)} seconds.')
        else:
            raise error

    @slash_util.slash_command(name='searchclan', description='Search up a clan in clash royale')
    @slash_util.describe(name='The clans name',
                         location='The clan location',
                         min='The minimum amount of members',
                         max='The maximum amount of members',
                         score='The minimum clan score',
                         result='The result to give back')
    async def _search_clan(self,
                           ctx,
                           name: str = None,
                           location: str = None,
                           min: int = None,
                           max: int = None,
                           score: int = None,
                           result: slash_util.Range[1, 10] = 1
                           ):
        if not location and not name and not min and not max and not score:
            return await ctx.send('You must give me an argument. (other than result)', ephemeral=True)
        if location is not None:
            try:
                location = int(location)
            except ValueError:
                pass
        if isinstance(location, str):
            location = locations.get(location.lower())
            if location is None:
                raise CountryError()
        elif isinstance(location, int):
            pass
        clans = await self.http.clans_request(name=name,
                                              locationId=location,
                                              minMembers=min,
                                              maxMembers=max,
                                              minScore=score)
        try:
            clan = clans[result - 1]
        except IndexError:
            return await ctx.send('Not enough clans were found.')
        await self._clan.func(self, ctx, clan.get('tag'))


def setup(bot: MasterBot):
    bot.add_cog(ClashRoyale(bot))
