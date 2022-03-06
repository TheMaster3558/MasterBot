import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils.view import View
from bot import MasterBot
import asyncio
import time
import datetime
from cogs.utils.help_utils import HelpSingleton
from cogs.utils.cog import Cog
from cogs.utils.modal import Modal


class Help(metaclass=HelpSingleton):
    def __init__(self, prefix):
        self.prefix = prefix

    def form_help(self):
        message = f'`{self.prefix}form <title> [expires_in_hours]`: Create a form for other users to take.'
        return message

    def takeform_help(self):
        message = f'`{self.prefix}takeform`: Take a form from another user!'
        return message

    def full_help(self):
        help_list = [self.form_help(), self.takeform_help()]
        return '\n'.join(help_list) + '\nAvailable with message commands soon.'


class QuestionView(View):
    def __init__(self):
        self.value = None
        super().__init__(timeout=30)

    @discord.ui.button(label='Short', style=discord.ButtonStyle.grey)
    async def short(self, button, interaction):
        self.value = discord.TextStyle.short
        await self.disable_all(interaction.message)
        self.stop()

    @discord.ui.button(label='Paragraph', style=discord.ButtonStyle.blurple)
    async def paragraph(self, button, interaction):
        self.value = discord.TextStyle.paragraph
        await self.disable_all(interaction.message)
        self.stop()


class FormSelect(discord.ui.Select['FormView']):
    def __init__(self, forms, author):
        self.author = author
        options = [discord.SelectOption(label=f'{form.title}') for form in forms]
        super().__init__(placeholder='Select a Form',
                         min_values=1,
                         max_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return interaction.response.send_message('This is not for you.',
                                                     ephemeral=True)
        await self.view.disable_all(interaction.message)
        self.view.stop()


class FormView(View):
    def __init__(self, forms, author):
        super().__init__(timeout=30)
        self.item = self.add_item(FormSelect(forms, author))


class ConfirmView(View):
    def __init__(self, modal, bot, cmd):
        self.modal = modal
        self.bot = bot
        self.cmd = cmd
        self.response = None
        self.interaction = None
        super().__init__(timeout=30)

    @discord.ui.button(label='Start', style=discord.ButtonStyle.green)
    async def confirm(self, button, interaction: discord.Interaction):
        #  saying interaction has already been responded to unless i make a new interaction
        await interaction.response.send_modal(self.modal)
        try:
            self.interaction = await self.modal.wait(timeout=600)
        except asyncio.TimeoutError:
            return
        self.response = self.modal.response
        await self.disable_all(interaction.message)
        self.stop()


class Forms(Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.modal: dict[int, list[discord.ui.Modal]] = {}
        self.results: dict[discord.ui.Modal, list[dict]] = {}
        print('Forms cog loaded')

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.modal[guild.id] = []

    @app_commands.command(description='Create a form for other users to take')
    @app_commands.describe(title='The title', expire='The hours it will expire in. Defaults to 3.')
    async def form(self,
                   ctx,
                   title: str,
                   expire: discord.app_commands.Range[int, 1, 48] = 3):
        if not ctx.guild:
            return await ctx.send('Try this in a server.')
        questions = []
        await ctx.send('Type `stop` when you want to finish the form.')
        while True:
            await ctx.send('Type a question:')
            msg = await self.bot.wait_for('message',
                                          check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if msg.content == 'stop':
                if len(questions) < 1:
                    return await ctx.send('You need over 0 questions?')
                break
            view = QuestionView()
            embed = discord.Embed(title='Select the type of question',
                                  description=msg.content)
            embed.set_footer(text='You have 30 seconds')
            await ctx.send(embed=embed, view=view)
            await view.wait()
            if view.value is None:
                return await ctx.send("You didn't click anything :(")
            questions.append((msg.content, view.value))
        # prepare for a nested class
        items = [discord.ui.TextInput(custom_id=question,
                                      label=question,
                                      style=style) for question, style in questions]
        modal = Modal(title=title, items=items)
        self.modal[ctx.guild.id].append(modal)
        now = datetime.datetime.now() + datetime.timedelta(hours=expire)  # type: ignore
        expire_time = round(time.mktime(now.timetuple()))
        embed = discord.Embed(title='Ok! Users can now use `/takeform` to take this form',
                              description=f'expires <t:{expire_time}:R>')
        await ctx.send(embed=embed)
        await asyncio.sleep(expire * 3600)  # type: ignore
        self.modal[ctx.guild.id].remove(modal)
        results = self.results.get(modal)
        if not results:
            return await ctx.author.send('Your form got no responses :(')
        embed = discord.Embed(title=f'Results for {title}')
        results_dict = {}
        for question, _ in questions:
            results_dict[question] = []
        for result in results:
            for k, v in result.items():
                results_dict[k].append(v)
        for k, v in results_dict.items():
            embed.add_field(name=k, value='\n'.join(v))
        await ctx.send(embed=embed)

    @app_commands.command(description='Take a form from another user!')
    async def takeform(self, ctx):
        if not ctx.guild:
            return await ctx.send('Try this in a server.')
        modals = self.modal[ctx.guild.id]
        if len(modals) == 0:
            return await ctx.send('There are no forms to take.')
        view = FormView(modals, ctx.author)
        msg = await ctx.send('Select one', view=view)
        await view.wait()
        try:
            value = view.item.values[0]
        except IndexError:
            return await ctx.send('You did not choose anything')
        modal = None
        for m in modals:
            if m.title == value:
                modal = m
                break
        view = ConfirmView(modal, self.bot, ctx.command)
        await msg.edit('Click to start! Your results will be anonymously sent to the creator of this form.', view=view)
        await view.wait()
        if view.modal.response is None:
            return
        if view.modal not in self.modal[ctx.guild.id]:
            return
        response = view.modal.response
        if modal not in self.results:
            self.results[modal] = []
        self.results[modal].append(response)
        await view.interaction.response.send_message('Your response has been recorded.')


def setup(bot: MasterBot):
    bot.add_cog(Forms(bot))
