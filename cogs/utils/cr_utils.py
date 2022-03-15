import discord
import re


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
        members = ['{} | {}'.format(member.get('name'), member.get('trophies')) for member in members[:5]]
        if clan.get('members') >= 5:
            embed.add_field(name='Top Members', value='\n'.join(members))
        embed.set_thumbnail(url='https://www.deckshop.pro/img/badges/{0}.png'.format(clan.get('badgeId')))
        return embed
