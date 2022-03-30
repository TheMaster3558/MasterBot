import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils.view import View
from bot import MasterBot
import asyncio
import time
import datetime
from cogs.utils.app_and_cogs import Cog, command, app_guild_only
from cogs.utils.modal import Modal


class QuestionView(View):
    def __init__(self):
        self.value = None
        super().__init__(timeout=30)

    @discord.ui.button(label='Short', style=discord.ButtonStyle.grey)
    async def short(self, interaction, button):
        self.value = discord.TextStyle.short
        await self.disable_all(interaction.message)
        self.stop()

    @discord.ui.button(label='Paragraph', style=discord.ButtonStyle.blurple)
    async def paragraph(self, interaction, button):
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
    def __init__(self, modal):
        self.modal = modal
        self.response = None
        self.interaction = None
        super().__init__(timeout=30)

    @discord.ui.button(label='Start', style=discord.ButtonStyle.green)
    async def confirm(self, interaction, button):
        #  saying interaction has already been responded to unless i make a new interaction
        await interaction.response.send_modal(self.modal)
        try:
            self.interaction = await self.modal.wait(timeout=600)
        except asyncio.TimeoutError:
            return
        self.response = self.modal.response
        await self.disable_all(interaction.message)
        self.stop()


class Forms(Cog, name='forms'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.modal: dict[int, list[discord.ui.Modal]] = {}
        self.results: dict[discord.ui.Modal, list[dict]] = {}
        print('Forms cog loaded')

    @commands.Cog.listener()
    async def on_ready(self):
        #  when discord.py adds setup function this will be removed because on_ready can be called many times
        for guild in self.bot.guilds:
            self.modal[guild.id] = []

    async def cog_command_error(self, ctx, error):
        error: commands.CommandError  # showing as `Exception` for some reason

        if not ctx.command:
            return
        if ctx.command.cog != self:
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(str(error))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send('Try this in a server')
        else:
            await self.bot.on_command_error(ctx, error)

    @commands.command(description='Create a form for other users to take. Anonymous.')
    @commands.guild_only()
    async def form(self, ctx, title, expire: int = 3):
        if expire > 48:
            await ctx.send("`expire` cannot be over 48 hours.")
            return
        questions = []
        await ctx.send('Type `stop` when you want to finish the form.')
        while True:
            await ctx.send('Type a question:')
            msg = await self.bot.wait_for('message',
                                          check=lambda
                                          m: m.author == ctx.author and m.channel == ctx.channel)
            if msg.content == 'stop':
                if len(questions) < 1:
                    await ctx.send('You need over 0 questions?')
                    return
                break
            view = QuestionView()
            embed = discord.Embed(title='Select the type of question',
                                  description=msg.content)
            embed.set_footer(text='You have 30 seconds')
            await ctx.send(embed=embed, view=view)
            await view.wait()
            if view.value is None:
                await ctx.send("You didn't click anything :(")
                return
            questions.append((msg.content, view.value))
        #  copies the dynamic slash_util modal instead of the discord.py modal
        items = [discord.ui.TextInput(custom_id=question,
                                      label=question,
                                      style=style) for question, style in questions]
        modal = Modal(title=title, items=items)
        self.modal[ctx.guild.id].append(modal)
        now = datetime.datetime.now() + datetime.timedelta(hours=expire)  # type: ignore
        expire_time = round(time.mktime(now.timetuple()))
        embed = discord.Embed(title=f'Ok! Users can now use `{ctx.clean_prefix}takeform` to take this form',
                              description=f'expires <t:{expire_time}:R>')
        await ctx.send(embed=embed)
        await asyncio.sleep(expire * 3600)  # type: ignore
        self.modal[ctx.guild.id].remove(modal)
        results = self.results.get(modal)
        if not results:
            await ctx.author.send('Your form got no responses :(')
            return
        embed = discord.Embed(title=f'Results for {title}')
        results_dict = {}
        for question, _ in questions:
            results_dict[question] = []
        for result in results:
            for k, v in result.items():
                results_dict[k].append(v)
        for k, v in results_dict.items():
            embed.add_field(name=k, value='\n'.join(v))
        await ctx.author.send(embed=embed)

    @command(name='form', description='Create a form for other users to take.')
    @app_commands.describe(title='The title', expire='The hours it will expire in. Defaults to 3.')
    @app_guild_only()
    async def _form(self,
                    interaction,
                    title: str,
                    expire: discord.app_commands.Range[int, 1, 48] = 3):
        if not interaction.guild:
            await interaction.response.send_message('Try this in a server.', ephemeral=True)
            return
        questions = []
        await interaction.response.send_message('Type `stop` when you want to finish the form.')
        while True:
            await interaction.followup.send('Type a question:')
            msg = await self.bot.wait_for('message',
                                          check=lambda
                                          m: m.author == interaction.user and m.channel == interaction.channel)
            if msg.content == 'stop':
                if len(questions) < 1:
                    await interaction.followup.send('You need over 0 questions?')
                    return
                break
            view = QuestionView()
            embed = discord.Embed(title='Select the type of question',
                                  description=msg.content)
            embed.set_footer(text='You have 30 seconds')
            await interaction.followup.send(embed=embed, view=view)
            await view.wait()
            if view.value is None:
                await interaction.followup.send("You didn't click anything :(")
                return
            questions.append((msg.content, view.value))
        #  copies the dynamic slash_util modal instead of the discord.py modal
        items = [discord.ui.TextInput(custom_id=question,
                                      label=question,
                                      style=style) for question, style in questions]
        modal = Modal(title=title, items=items)
        self.modal[interaction.guild.id].append(modal)
        now = datetime.datetime.now() + datetime.timedelta(hours=expire)  # type: ignore
        expire_time = round(time.mktime(now.timetuple()))
        embed = discord.Embed(title='Ok! Users can now use `/takeform` to take this form',
                              description=f'expires <t:{expire_time}:R>')
        await interaction.followup.send(embed=embed)
        await asyncio.sleep(expire * 3600)  # type: ignore
        self.modal[interaction.guild.id].remove(modal)
        results = self.results.get(modal)
        if not results:
            await interaction.user.send('Your form got no responses :(')
            return
        embed = discord.Embed(title=f'Results for {title}')
        results_dict = {}
        for question, _ in questions:
            results_dict[question] = []
        for result in results:
            for k, v in result.items():
                results_dict[k].append(v)
        for k, v in results_dict.items():
            embed.add_field(name=k, value='\n'.join(v))
        await interaction.user.send(embed=embed)

    @commands.command(description='Take a form anonymously from another user.')
    @commands.guild_only()
    async def takeform(self, ctx):
        modals = self.modal[ctx.guild.id]
        if len(modals) == 0:
            await ctx.send('There are no forms to take.')
            return
        view = FormView(modals, ctx.author)
        msg = await ctx.send('Select one', view=view)
        await view.wait()
        try:
            value = view.item.values[0]
        except IndexError:
            await msg.reply('You did not choose anything')
            return
        modal = None
        for m in modals:
            if m.title == value:
                modal = m
                break
        view = ConfirmView(modal)
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

    @command(name='takeform', description='Take a form from another user!')
    @app_guild_only()
    async def _takeform(self, interaction):
        if not interaction.guild:
            await interaction.response.send_message('Try this in a server.')
            return
        modals = self.modal[interaction.guild.id]
        if len(modals) == 0:
            await interaction.response.send_message('There are no forms to take.')
            return
        view = FormView(modals, interaction.user)
        msg = await interaction.response.send_message('Select one', view=view)
        await view.wait()
        try:
            value = view.item.values[0]
        except IndexError:
            await interaction.followup.send('You did not choose anything')
            return
        modal = None
        for m in modals:
            if m.title == value:
                modal = m
                break
        view = ConfirmView(modal)
        await msg.edit('Click to start! Your results will be anonymously sent to the creator of this form.', view=view)
        await view.wait()
        if view.modal.response is None:
            return
        if view.modal not in self.modal[interaction.guild.id]:
            return
        response = view.modal.response
        if modal not in self.results:
            self.results[modal] = []
        self.results[modal].append(response)
        await view.interaction.response.send_message('Your response has been recorded.')


async def setup(bot: MasterBot):
    await Forms.setup(bot)
