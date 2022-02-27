# -*- coding: utf-8 -*-

from __future__ import annotations

import discord
from discord.ext import commands
import slash_util
from bot import MasterBot
from cogs.utils.view import View


class TicTacToeButton(discord.ui.Button['TicTacToeView']):
    emojis = {0: '❌', 1: '⭕'}

    def __init__(self, x, y):
        self.x, self.y = x, y
        super().__init__(style=discord.ButtonStyle.grey, row=y, label='\u0020')

    async def callback(self, interaction: discord.Interaction):
        if self.view.users[self.view.turn] == interaction.user.id:
            self.label = self.emojis[self.view.turn]
            for child in self.view.children:
                if (child.x, child.y) == (self.x, self.y):  # type: ignore
                    self.disabled = True
                    break
            await self.view.msg.edit(view=self.view)
            self.view.turn = 1 if self.view.turn == 0 else 0
            return
        if interaction.user.id in self.view.users:
            await interaction.response.send_message('Wait for your turn', ephemeral=True)
            return
        await interaction.response.send_message('You are not in this tic tac toe game')


class TicTacToeView(View):
    def __init__(self, user1, user2):
        self.users = [user1.id, user2.id]
        self.turn = 0
        self.msg: discord.Message = None  # type: ignore
        super().__init__()
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))


class Games(slash_util.Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        print('Games cog loaded')

    @commands.command()
    @commands.guild_only()
    async def tictactoe(self, ctx, member: discord.Member=None):
        member = member or ctx.author
        view = TicTacToeView(ctx.author, member)
        embed = discord.Embed(title=f'{ctx.author.display_name} vs {member.display_name}')
        msg = await ctx.send(embed=embed, view=view)
        view.msg = msg


def setup(bot: MasterBot):
    bot.add_cog(Games(bot))
