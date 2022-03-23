import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils.http import AsyncHTTPClient
from cogs.utils.app_and_cogs import Cog
from bot import MasterBot
from cogs.utils.view import View
from typing import Literal


class FBIHTTPClient(AsyncHTTPClient):
    types = ('Main', 'Victim', 'Accomplice')
    statuses = ('captured', 'recovered', 'located', 'surrendered', 'deceased')

    def __init__(self, loop):
        super().__init__('https://api.fbi.gov', loop=loop)

    async def general_wanted(self, *, title: str = None, person: str = None, status: str = None):
        return await self.request(
            '/@wanted',
            json=False,
            title=title,
            person_classification=person,
            status=status,
            pageSize=20,
            page=1,
            sort_on='modified',
            sort_order='desc'
        )

    async def id_wanted(self, uid: str):
        #  different type of request this time
        async with self.session.get(self.base + '/@wanted/' + uid) as resp:
            data = await resp.json()
            if resp.status == 404:
                raise discord.NotFound(resp, data.get('reason'))
            return data


class StandardSelect(discord.ui.Select['FBIView']):
    def __init__(self, option: Literal["types", "statuses"]):
        options = [discord.SelectOption(label='Any')] + [discord.SelectOption(label=label) for label in getattr(
            FBIHTTPClient, option)]
        super().__init__(options=options, min_values=1)
        self.failed = False

    async def callback(self, interaction: discord.Interaction):
        if len(self.values) > 1 and 'Any' in self.values:
            await interaction.response.send_message("You can't select `Any` and other options.", ephemeral=True)
            self.failed = True
            await self.view.disable_all(interaction.message)
            self.view.stop()
            return
        await interaction.response.send_message('Ok!', ephemeral=True)
        self.disabled = True
        await interaction.message.edit(view=self.view)
        await self.check_if_finished(interaction)

    async def check_if_finished(self, interaction: discord.Interaction):
        for child in self.view.children:
            if not child.disabled:  # type: ignore
                return
        await self.view.disable_all(interaction.message)
        self.view.stop()


class FBIView(View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.person = self.add_item(StandardSelect('types'))
        self.status = self.add_item(StandardSelect('statuses'))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message('This is not for you', ephemeral=True)
            return False
        return True


class FBIWanted(Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.http = FBIHTTPClient(loop=self.bot.loop)
        print('FBI wanted cog loaded')

    @commands.command()
    async def wanted(self, ctx, title: str):
        view = FBIView(ctx.author)
        await ctx.send('Pick some choices.', view=view)
        await view.wait()

        person = view.person.values[0]
        if person == 'Any':
            person = None
        status = view.status.values[0]
        if status == 'Any':
            status = None
        data = await self.http.general_wanted(
            title=title,
            person=person,
            status=status
        )
        print(data)


def setup(bot: MasterBot):
    bot.add_cog(FBIWanted(bot))


