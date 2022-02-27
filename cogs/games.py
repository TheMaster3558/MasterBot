# -*- coding: utf-8 -*-

from __future__ import annotations

import discord
from discord.ext import commands
import slash_util
from bot import MasterBot
from cogs.utils.view import View
from typing import Literal
import asyncio


Num = Literal[0, 1, 2]


class TicTacToeButton(discord.ui.Button['TicTacToeView']):
    emojis = {0: '❌', 1: '⭕'}

    def __init__(self, x, y):
        self.x, self.y = x, y
        super().__init__(style=discord.ButtonStyle.grey, row=y, label='\u0020')

    async def callback(self, interaction: discord.Interaction):
        self.label = self.emojis[self.view.turn]
        for child in self.view.children:
            if (child.x, child.y) == (self.x, self.y):  # type: ignore
                self.disabled = True
                break
        if self.view.turn == 0:
            self.view.x.append((self.x, self.y))
            player = 'x'
        else:
            self.view.o.append((self.x, self.y))
            player = 'o'
        finished = False
        moves = getattr(self.view, player)
        for combo in self.view.diags:
            if all([c in moves for c in combo]):
                finished = True
                self.view.winner = self.view.users[self.view.turn]
                child: TicTacToeButton
                for child in self.view.children:
                    if (child.x, child.y) in combo:
                        child.style = discord.ButtonStyle.green
                break

        if not finished:
            counter_x = {0: 0, 1: 0, 2: 0}
            counter_y = {0: 0, 1: 0, 2: 0}
            for x, y in moves:
                counter_x[x] += 1
                counter_y[y] += 1
            for k, v in counter_x.items():
                if v == 3:
                    finished = True
                    self.view.winner = self.view.users[self.view.turn]
                    for child in self.view.children:
                        if child.x == k:
                            child.style = discord.ButtonStyle.green
                    break
            if not finished:
                for k, v in counter_y.items():
                    if v == 3:
                        finished = True
                        self.view.winner = self.view.users[self.view.turn]
                        for child in self.view.children:
                            if child.y == k:
                                child.style = discord.ButtonStyle.green
                        break

        await interaction.message.edit(view=self.view)
        if finished:
            await self.view.disable_all(interaction.message)
            self.view.stop()
        self.view.turn = 1 if self.view.turn == 0 else 0


class TicTacToeView(View):
    diags: list[list[tuple[Num, Num]]] = [  # each must be hardcoded sadly
        [(0, 0), (1, 1), (2, 2)],
        [(0, 0), (2, 2), (1, 1)],
        [(1, 1), (0, 0), (2, 2)],
        [(1, 1), (2, 2), (0, 0)],
        [(2, 2), (0, 0), (1, 1)],
        [(2, 2), (1, 1), (0, 0)],
        [(2, 0), (1, 1), (0, 2)],
        [(2, 0), (0, 2), (1, 1)],
        [(1, 1), (2, 0), (0, 2)],
        [(1, 1), (0, 2), (2, 0)],
        [(0, 2), (1, 1), (0, 2)],
        [(0, 2), (0, 2), (1, 1)],
    ]

    def __init__(self, user1, user2):
        self.users = [user1.id, user2.id]
        self.turn = 0
        self.winner = None
        self.x = []
        self.o = []
        super().__init__()
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.users[self.turn] == interaction.user.id:
            return True
        if interaction.user.id in self.users:
            await interaction.response.send_message('Wait for your turn', ephemeral=True)
            return False
        await interaction.response.send_message('You are not in this tic tac toe game')
        return False


class Games(slash_util.Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        print('Games cog loaded')

    @commands.command()
    @commands.guild_only()
    async def tictactoe(self, ctx, *, member: discord.Member):
        view = TicTacToeView(ctx.author, member)
        embed = discord.Embed(title=f'{ctx.author.display_name} vs {member.display_name}')
        embed.set_footer(text='You have 3 minutes.')
        msg = await ctx.send(embed=embed, view=view)
        await view.wait()
        await msg.reply(f'The winner is {view.winner}!')

    @tictactoe.error
    async def error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send('You only can do this in a server.')
        elif isinstance(error, commands.MemberNotFound):
            await ctx.reply("I couldn't find that member")
        elif isinstance(error, commands.MissingRequiredArgument):
            o_msg = await ctx.send('Mention a user')
            try:
                msg = await self.bot.wait_for('message',
                                              check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                                              timeout=30)
            except asyncio.TimeoutError:
                await o_msg.reply("You didn't respond in time.")
                return
            try:
                member = await commands.MemberConverter().convert(ctx, msg.content)
            except commands.MemberNotFound:
                await ctx.send("sadly I couldn't find that member")
                return
            await self.tictactoe(ctx, member=member)


def setup(bot: MasterBot):
    bot.add_cog(Games(bot))
