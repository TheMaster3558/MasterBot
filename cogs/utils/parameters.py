from operator import attrgetter

import discord
from discord.ext import commands


# only allow discord.Member
MemberAuthor = commands.parameter(
    default=attrgetter("author"), displayed_default="<you>", converter=discord.Member
)
