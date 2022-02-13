"""
The MIT License (MIT)

Copyright (c) 2021-present The Master

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


import discord
from discord.ext import commands
from masterbot.cogs.utils.http import AsyncHTTPClient
import asyncio
import random
from html import unescape
import slash_util
from masterbot.cogs.utils.view import View
from masterbot.bot import MasterBot


class Help:
    def __init__(self, prefix):
        self.prefix = prefix

    def trivia_help(self):
        message = f'`{self.prefix}trivia`: Get a trivia question. Many people can play!'
        return message

    def full_help(self):
        return self.trivia_help()


class OpenTDBHTTPClient(AsyncHTTPClient):
    def __init__(self):
        super().__init__('https://opentdb.com/')
        self.token = None

    async def trivia(self, amount=1):
        return await self.request('api.php', amount=amount, token=self.token)

    async def get_token(self):
        resp = await self.request('api_token.php', command='request')
        self.token = resp.get('token')


colors = [discord.ButtonStyle.green, discord.ButtonStyle.red, discord.ButtonStyle.blurple, discord.ButtonStyle.grey]


class TriviaButton(discord.ui.Button['MultipleChoice']):
    def __init__(self, choice, correct, color):
        self.correct = correct
        super().__init__(style=color, label=choice)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        if self.correct is True:
            self.view.done = True
            await self.view.disable_all(message=interaction.message)
            embed = discord.Embed(title=f'{interaction.user.display_name} got it right!',
                                  description=f'The answer was {self.label}')
            if len(self.view.tries) > 0:
                embed.add_field(name='Wrong guesses', value='\n'.join(f'{k}: {v}' for k, v in self.view.tries.items()))
            await interaction.response.send_message(embed=embed)
            return self.view.stop()
        await interaction.response.send_message('Wrong answer.', ephemeral=True)
        self.view.tries[interaction.user.display_name] = self.label


class MultipleChoice(View):
    def __init__(self, correct, incorrect: list):
        self.incorrect = incorrect
        self.choices: list = incorrect + [correct]
        self.choices = [unescape(choice) for choice in self.choices]
        random.shuffle(self.choices)
        self.done = False
        self.tries = {}
        super().__init__(timeout=30)
        for index, choice in enumerate(self.choices):
            answer = False
            if choice == correct:
                answer = True
            self.add_item(TriviaButton(choice, answer, colors[index]))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.done:
            self.stop()
            return False
        if interaction.user.display_name in self.tries.keys():
            await interaction.response.send_message('You already tried and failed.', ephemeral=True)
            return False
        return True


class Trivia(slash_util.Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = OpenTDBHTTPClient()
        asyncio.ensure_future(self.http.get_token())
        print('Trivia cog loaded')

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.channel)
    async def trivia(self, ctx):
        data = await self.http.trivia()
        if data.get('response_code') != 0:
            return await ctx.send('We encountered an unexpected error. Try again later.')
        data = data.get('results')[0]
        question = unescape(data.get('question'))
        embed = discord.Embed(title=question)
        embed.set_footer(text='The difficulty is {}'.format(data.get('difficulty')))
        my_view = MultipleChoice(data.get('correct_answer'), data.get('incorrect_answers'))
        message = await ctx.send(embed=embed, view=my_view)
        await my_view.wait()
        if my_view.done is False:
            await my_view.disable_all(message=message)
            embed = discord.Embed(title='No one got it right in time.',
                                  description='The answer was {}'.format(unescape(data.get('correct_answer'))))
            embed.add_field(name='Wrong guesses', value='\n'.join(f'{k}: {v}' for k, v in my_view.tries.items()) or 'No guesses')
            await message.reply(embed=embed)

    @trivia.error
    async def error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
        else:
            raise type(error)(error)

    @slash_util.slash_command(name='trivia', description='Get trivia from opentdb.com!')
    async def _trivia(self, ctx: slash_util.Context):
        await self.trivia(ctx)


def setup(bot: MasterBot):
    bot.add_cog(Trivia(bot))