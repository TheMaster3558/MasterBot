import discord
from discord.ext import commands
import slash_util
from typing import Optional, Union
from cogs.http import AsyncHTTPClient
from requests.structures import CaseInsensitiveDict
import re


class Help:
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
        """                name: str = None,
                           location: str = None,
                           min: int = None,
                           max: int = None,
                           score: int = None,
                           result: slash_util.Range[1, 10] = 1"""
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


locations = {'europe': 57000000, 'north america': 57000001, 'south america': 57000002, 'asia': 57000003, 'oceania': 57000004, 'africa': 57000005, 'international': 57000006, 'afghanistan': 57000007, 'åland islands': 57000008, 'albania': 57000009, 'algeria': 57000010, 'american samoa': 57000011, 'andorra': 57000012, 'angola': 57000013, 'anguilla': 57000014, 'antarctica': 57000015, 'antigua and barbuda': 57000016, 'argentina': 57000017, 'armenia': 57000018, 'aruba': 57000019, 'ascension island': 57000020, 'australia': 57000021, 'austria': 57000022, 'azerbaijan': 57000023, 'bahamas': 57000024, 'bahrain': 57000025, 'bangladesh': 57000026, 'barbados': 57000027, 'belarus': 57000028, 'belgium': 57000029, 'belize': 57000030, 'benin': 57000031, 'bermuda': 57000032, 'bhutan': 57000033, 'bolivia': 57000034, 'bosnia and herzegovina': 57000035, 'botswana': 57000036, 'bouvet island': 57000037, 'brazil': 57000038, 'british indian ocean territory': 57000039, 'british virgin islands': 57000040, 'brunei': 57000041, 'bulgaria': 57000042, 'burkina faso': 57000043, 'burundi': 57000044, 'cambodia': 57000045, 'cameroon': 57000046, 'canada': 57000047, 'canary islands': 57000048, 'cape verde': 57000049, 'caribbean netherlands': 57000050, 'cayman islands': 57000051, 'central african republic': 57000052, 'ceuta and melilla': 57000053, 'chad': 57000054, 'chile': 57000055, 'china': 57000056, 'christmas island': 57000057, 'cocos (keeling) islands': 57000058, 'colombia': 57000059, 'comoros': 57000060, 'congo (drc)': 57000061, 'congo (republic)': 57000062, 'cook islands': 57000063, 'costa rica': 57000064, 'côte d’ivoire': 57000065, 'croatia': 57000066, 'cuba': 57000067, 'curaçao': 57000068, 'cyprus': 57000069, 'czech republic': 57000070, 'denmark': 57000071, 'diego garcia': 57000072, 'djibouti': 57000073, 'dominica': 57000074, 'dominican republic': 57000075, 'ecuador': 57000076, 'egypt': 57000077, 'el salvador': 57000078, 'equatorial guinea': 57000079, 'eritrea': 57000080, 'estonia': 57000081, 'ethiopia': 57000082, 'falkland islands': 57000083, 'faroe islands': 57000084, 'fiji': 57000085, 'finland': 57000086, 'france': 57000087, 'french guiana': 57000088, 'french polynesia': 57000089, 'french southern territories': 57000090, 'gabon': 57000091, 'gambia': 57000092, 'georgia': 57000093, 'germany': 57000094, 'ghana': 57000095, 'gibraltar': 57000096, 'greece': 57000097, 'greenland': 57000098, 'grenada': 57000099, 'guadeloupe': 57000100, 'guam': 57000101, 'guatemala': 57000102, 'guernsey': 57000103, 'guinea': 57000104, 'guinea-bissau': 57000105, 'guyana': 57000106, 'haiti': 57000107, 'heard & mcdonald islands': 57000108, 'honduras': 57000109, 'hong kong': 57000110, 'hungary': 57000111, 'iceland': 57000112, 'india': 57000113, 'indonesia': 57000114, 'iran': 57000115, 'iraq': 57000116, 'ireland': 57000117, 'isle of man': 57000118, 'israel': 57000119, 'italy': 57000120, 'jamaica': 57000121, 'japan': 57000122, 'jersey': 57000123, 'jordan': 57000124, 'kazakhstan': 57000125, 'kenya': 57000126, 'kiribati': 57000127, 'kosovo': 57000128, 'kuwait': 57000129, 'kyrgyzstan': 57000130, 'laos': 57000131, 'latvia': 57000132, 'lebanon': 57000133, 'lesotho': 57000134, 'liberia': 57000135, 'libya': 57000136, 'liechtenstein': 57000137, 'lithuania': 57000138, 'luxembourg': 57000139, 'macau': 57000140, 'macedonia (fyrom)': 57000141, 'madagascar': 57000142, 'malawi': 57000143, 'malaysia': 57000144, 'maldives': 57000145, 'mali': 57000146, 'malta': 57000147, 'marshall islands': 57000148, 'martinique': 57000149, 'mauritania': 57000150, 'mauritius': 57000151, 'mayotte': 57000152, 'mexico': 57000153, 'micronesia': 57000154, 'moldova': 57000155, 'monaco': 57000156, 'mongolia': 57000157, 'montenegro': 57000158, 'montserrat': 57000159, 'morocco': 57000160, 'mozambique': 57000161, 'myanmar (burma)': 57000162, 'namibia': 57000163, 'nauru': 57000164, 'nepal': 57000165, 'netherlands': 57000166, 'new caledonia': 57000167, 'new zealand': 57000168, 'nicaragua': 57000169, 'niger': 57000170, 'nigeria': 57000171, 'niue': 57000172, 'norfolk island': 57000173, 'north korea': 57000174, 'northern mariana islands': 57000175, 'norway': 57000176, 'oman': 57000177, 'pakistan': 57000178, 'palau': 57000179, 'palestine': 57000180, 'panama': 57000181, 'papua new guinea': 57000182, 'paraguay': 57000183, 'peru': 57000184, 'philippines': 57000185, 'pitcairn islands': 57000186, 'poland': 57000187, 'portugal': 57000188, 'puerto rico': 57000189, 'qatar': 57000190, 'réunion': 57000191, 'romania': 57000192, 'russia': 57000193, 'rwanda': 57000194, 'saint barthélemy': 57000195, 'saint helena': 57000196, 'saint kitts and nevis': 57000197, 'saint lucia': 57000198, 'saint martin': 57000199, 'saint pierre and miquelon': 57000200, 'samoa': 57000201, 'san marino': 57000202, 'são tomé and príncipe': 57000203, 'saudi arabia': 57000204, 'senegal': 57000205, 'serbia': 57000206, 'seychelles': 57000207, 'sierra leone': 57000208, 'singapore': 57000209, 'sint maarten': 57000210, 'slovakia': 57000211, 'slovenia': 57000212, 'solomon islands': 57000213, 'somalia': 57000214, 'south africa': 57000215, 'south korea': 57000216, 'south sudan': 57000217, 'spain': 57000218, 'sri lanka': 57000219, 'st. vincent & grenadines': 57000220, 'sudan': 57000221, 'suriname': 57000222, 'svalbard and jan mayen': 57000223, 'swaziland': 57000224, 'sweden': 57000225, 'switzerland': 57000226, 'syria': 57000227, 'taiwan': 57000228, 'tajikistan': 57000229, 'tanzania': 57000230, 'thailand': 57000231, 'timor-leste': 57000232, 'togo': 57000233, 'tokelau': 57000234, 'tonga': 57000235, 'trinidad and tobago': 57000236, 'tristan da cunha': 57000237, 'tunisia': 57000238, 'turkey': 57000239, 'turkmenistan': 57000240, 'turks and caicos islands': 57000241, 'tuvalu': 57000242, 'u.s. outlying islands': 57000243, 'u.s. virgin islands': 57000244, 'uganda': 57000245, 'ukraine': 57000246, 'united arab emirates': 57000247, 'united kingdom': 57000248, 'united states': 57000249, 'uruguay': 57000250, 'uzbekistan': 57000251, 'vanuatu': 57000252, 'vatican city': 57000253, 'venezuela': 57000254, 'vietnam': 57000255, 'wallis and futuna': 57000256, 'western sahara': 57000257, 'yemen': 57000258, 'zambia': 57000259, 'zimbabwe': 57000260}


class ClashRoyaleUtils:
    """
    A class to help build embeds and other helpful functions.
    No instance required. All methods are static.
    """
    @staticmethod
    async def build_player_embed(player: dict) -> discord.Embed:
        embed = discord.Embed(title='{0} {1}'.format(player.get('name'), player.get('tag')))
        embed.add_field(name='King Level', value=player.get('expLevel'))
        embed.add_field(name='Current Trophies', value=player.get('trophies'))
        try:
            embed.add_field(name='Season High',
                            value=player.get('leagueStatistics').get('currentSeason').get('bestTrophies'))
        except AttributeError:
            embed.add_field(name='Season High', value='N/A')
        try:
            embed.add_field(name='Previous Season',
                            value=player.get('leagueStatistics').get('previousSeason').get('trophies'))
        except AttributeError:
            embed.add_field(name='Previous Season', value='N/A')
        embed.add_field(name='Highest Trophies', value=player.get('bestTrophies'))
        embed.add_field(name='Arena', value=player.get('arena').get('name'))
        embed.add_field(name='Wins', value=player.get('wins'))
        embed.add_field(name='Losses', value=player.get('losses'))
        ladder_battle_count = player.get('wins') + player.get('losses')
        embed.add_field(name='Winrate', value='{}%'.format(round((player.get('wins') / ladder_battle_count) * 100, 1)))
        embed.add_field(name='Total Battle Count', value=player.get('battleCount'))
        embed.add_field(name='Three Crowns', value=player.get('threeCrownWins'))
        embed.add_field(name='Max Challenge Wins', value=player.get('challengeMaxWins'))
        embed.add_field(name='Challenge Cards Won', value=player.get('challengeCardsWon'))
        embed.add_field(name='Total Donations', value=player.get('totalDonations'))
        embed.add_field(name='Star Points', value=player.get('starPoints') or 'N/A')
        embed.add_field(name='CW1 Warday Wins', value=player.get('warDayWins'))
        embed.add_field(name='CW1 Clan Cards Collected', value=player.get('clanCardsCollected'))
        role = player.get('role')
        if role == 'coLeader':
            role = 'co-leader'
        role = list(role)
        role[0] = role[0].upper()
        role = ''.join(role)
        embed.add_field(name=f'{role} in',
                        value='[{0}](https://royaleapi.com/clan/{1})'.format(player.get('clan').get('name'),
                                                                                    player.get('clan').get('tag')[1:]))
        age = 'Unknown'
        for badge in player.get('badges'):
            if badge.get('name') == 'Played1Year':
                age = badge.get('progress')
                y = age // 365
                m = (age - y * 365) // 30
                d = (age - y * 365 - m * 30)
                age = '{0} years {1} months {2} days'.format(y, m, d)
                break
        embed.add_field(name='Account Age', value=age)
        badges = [badge.get('name') if not badge.get('level') else '{0} **Level: {1}**'.format(badge.get('name'),
                                                                                               badge.get('level')) for badge
                  in player.get('badges')]
        badges = [re.sub('(\d+(\.\d+)?)', r' \1 ', badge) for badge in badges]
        try:
            badges.remove('TopLeague')
        except ValueError:
            pass
        embed.add_field(name='Badges', value=', '.join(badges) or 'None')
        current_deck = [card.get('name') for card in player.get('currentDeck')]
        embed.add_field(name='Current Deck', value=', '.join(current_deck))
        embed.set_thumbnail(
            url='https://th.bing.com/th/id/R.dc47e311fb4fb32c139c5a4146e020a8?rik=hu1IfHDubAYwuQ&riu=http%3a%2f%2fvignette4.wikia.nocookie.net%2fclashroyale%2fimages%2fe%2fed%2fLegendary_Arena.png%2frevision%2flatest%3fcb%3d20160218170847&ehk=Y%2bGqOSGsU0zs9IdWUUFM0jhEBL8WKy7D3Ki81xm2Ovc%3d&risl=&pid=ImgRaw&r=0')
        return embed

    @staticmethod
    def search_for_card(cards: list, name: str) -> dict:
        for card in cards:
            if card.get('name').lower() == name.lower():
                return card
        raise ValueError("Hey! That's not a real card.")

    @staticmethod
    async def build_card_embed(card: dict) -> discord.Embed:
        embed = discord.Embed(title=card.get('name'))
        embed.add_field(name='Max Level', value=card.get('maxLevel'))
        embed.set_image(url=card.get('iconUrls').get('medium'))
        return embed

    @staticmethod
    async def build_clan_embed(clan: dict) -> discord.Embed:
        embed = discord.Embed(title='{0} {1}'.format(clan.get('name'), clan.get('tag')))
        embed.add_field(name='Score', value=clan.get('clanScore'))
        embed.add_field(name='Clan War Trophies', value=clan.get('clanWarTrophies'))
        embed.add_field(name='Location', value=clan.get('location').get('name'))
        embed.add_field(name='Required Trophies', value=clan.get('requiredTrophies'))
        embed.add_field(name='Donations Per Week', value=clan.get('donationsPerWeek'))
        leader = None
        members = clan.get('memberList')
        for member in members:
            if member.get('role') == 'leader':
                leader = member
        embed.add_field(name="Leader", value='[{0}](https://royaleapi.com/player/{1})'.format(leader.get('name'), leader.get('tag')[1:]))
        trophy_range = '{0}-{1}'.format(members[-1].get('trophies'), members[0].get('trophies'))
        embed.add_field(name='Trophy Range', value=trophy_range)
        embed.add_field(name='Members', value='{0}/50'.format(clan.get('members')))
        if clan.get('type') == 'inviteOnly':
            clan['type'] = 'invite only'
        t = list(clan['type'])
        t[0] = t[0].upper()
        t = ''.join(t)
        embed.add_field(name='Join Status', value=t)
        embed.add_field(name='Description', value='{}'.format(clan.get('description')))
        members = clan.get('memberList')
        members = ['{} | {} 🏆'.format(member.get('name'), member.get('trophies')) for member in members[:5]]
        if clan.get('members') >= 5:
            embed.add_field(name='Top Members', value='\n'.join(members))
        embed.set_thumbnail(url='https://www.deckshop.pro/img/badges/{0}.png'.format(clan.get('badgeId')))
        return embed


class ClashRoyaleHTTPClient(AsyncHTTPClient):
    def __init__(self, api_key):
        self.api_key = api_key
        headers = CaseInsensitiveDict()
        headers['Authorization'] = f'Bearer {api_key}'
        headers['content-type'] = 'application/json'
        super().__init__('https://api.clashroyale.com/v1/', headers=headers)

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


class ClashRoyale(slash_util.ApplicationCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.api_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6Ijc5MjhjYTgyLTQzOTYtNDBhMS1hOGFjLTkxYTkyZmRlZDFjYSIsImlhdCI6MTYzNzk2NTE5Niwic3ViIjoiZGV2ZWxvcGVyL2U2ZGEwOWQ3LTg1ZjItMDQxOC1mODI5LWQyNjU3OGRlNGIyYiIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyI3Ni4xMDQuMjQ2LjEyNyJdLCJ0eXBlIjoiY2xpZW50In1dfQ.3fLriIL4gEg6-xqJ6SJe56s6kZNP8FvQ8yUr6dAQZDdeCYiectFfRw_q3mj8Lipj0R6BW1k25z-j-zWrLfheYA'
        self.http = ClashRoyaleHTTPClient(self.api_key)
        print('Clash Royale cog loaded')

    @commands.command()
    async def crlocations(self, ctx):
        global locations
        cr_locations = ', '.join(k for k in locations.keys())
        embed = discord.Embed(title='Clash Royale location list',
                              description=cr_locations)
        await ctx.author.send(embed=embed)

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
        if isinstance(error, commands.CommandOnCooldown):
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


def setup(bot: commands.Bot):
    bot.add_cog(ClashRoyale(bot))
