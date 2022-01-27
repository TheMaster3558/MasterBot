import discord
from discord.ext import commands
from cogs.utils.http import AsyncHTTPClient
import asyncio
import random
from html import unescape
import slash_util
from cogs.utils.view import View


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


def view(correct: str, wrong: list):
    choices = wrong + [correct]
    choices = [unescape(choice) for choice in choices]
    random.shuffle(choices)

    class MultipleChoice(View):
        def __init__(self):
            self.tries = {}
            self.done = False
            super().__init__(timeout=30)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if self.done:
                self.stop()
                return False
            if interaction.user.display_name in self.tries.keys():
                await interaction.response.send_message('You already tried and failed.', ephemeral=True)
                return False
            return True

        @discord.ui.button(style=discord.ButtonStyle.red, label=choices[0])
        async def choice1(self, button: discord.ui.Button, interaction: discord.Interaction):
            if button.label == correct:
                self.done = True
                await self.disable_all(message=interaction.message)
                embed = discord.Embed(title=f'{interaction.user.display_name} got it right!',
                                      description=f'The answer was {correct}')
                if len(self.tries) > 0:
                    embed.add_field(name='Wrong guesses', value='\n'.join(f'{k}: {v}' for k, v in self.tries.items()))
                await interaction.response.send_message(embed=embed)
                return self.stop()
            await interaction.response.send_message('Wrong answer.', ephemeral=True)
            self.tries[interaction.user.display_name] = button.label

        @discord.ui.button(style=discord.ButtonStyle.green, label=choices[1])
        async def choice2(self, button: discord.ui.Button, interaction: discord.Interaction):
            if button.label == correct:
                self.done = True
                await self.disable_all(message=interaction.message)
                embed = discord.Embed(title=f'{interaction.user.display_name} got it right!',
                                      description=f'The answer was {correct}')
                if len(self.tries) > 0:
                    embed.add_field(name='Wrong guesses', value='\n'.join(f'{k}: {v}' for k, v in self.tries.items()))
                await interaction.response.send_message(embed=embed)
                return self.stop()
            await interaction.response.send_message('Wrong answer.', ephemeral=True)
            self.tries[interaction.user.display_name] = button.label

        if len(choices) > 2:
            @discord.ui.button(style=discord.ButtonStyle.blurple, label=choices[2])
            async def choice3(self, button: discord.ui.Button, interaction: discord.Interaction):
                if button.label == correct:
                    self.done = True
                    await self.disable_all(message=interaction.message)
                    embed = discord.Embed(title=f'{interaction.user.display_name} got it right!',
                                          description=f'The answer was {correct}')
                    if len(self.tries) > 0:
                        embed.add_field(name='Wrong guesses',
                                        value='\n'.join(f'{k}: {v}' for k, v in self.tries.items()))
                    await interaction.response.send_message(embed=embed)
                await interaction.response.send_message('Wrong answer.', ephemeral=True)
                self.tries[interaction.user.display_name] = button.label

        if len(choices) > 3:
            @discord.ui.button(style=discord.ButtonStyle.gray, label=choices[3])
            async def choice4(self, button: discord.ui.Button, interaction: discord.Interaction):
                if button.label == correct:
                    self.done = True
                    await self.disable_all(message=interaction.message)
                    embed = discord.Embed(title=f'{interaction.user.display_name} got it right!',
                                          description=f'The answer was {correct}')
                    if len(self.tries) > 0:
                        embed.add_field(name='Wrong guesses',
                                        value='\n'.join(f'{k}: {v}' for k, v in self.tries.items()))
                    await interaction.response.send_message(embed=embed)
                    return self.stop()
                await interaction.response.send_message('Wrong answer.', ephemeral=True)
                self.tries[interaction.user.display_name] = button.label

    return MultipleChoice()


class Trivia(slash_util.ApplicationCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.http = OpenTDBHTTPClient()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.http.get_token())
        print('Trivia cog loaded')

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.channel)
    async def trivia(self, ctx):
        data = await self.http.trivia()
        if data.get('response_code') != 0:
            print(data)
            return await ctx.send('We encountered an unexpected error. Try again later.')
        data = data.get('results')[0]
        question = unescape(data.get('question'))
        embed = discord.Embed(title=question)
        embed.set_footer(text='The difficulty is {}'.format(data.get('difficulty')))
        my_view = view(data.get('correct_answer'), data.get('incorrect_answers'))
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
    async def _trivia(self, ctx):
        await self.trivia(ctx)


def setup(bot: commands.Bot):
    bot.add_cog(Trivia(bot))
