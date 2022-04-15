from __future__ import annotations

from typing import Optional
import asyncio

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import aiosqlite
from aiosqlite import IntegrityError

from bot import MasterBot
from cogs.utils.app_and_cogs import Cog, NoPrivateMessage
from cogs.utils.view import View, smart_send


MISSING = discord.utils.MISSING


class WebhookUserFlags(commands.FlagConverter):
    name: str
    avatar: Optional[str] = None


class ConfirmView(View):
    def __init__(self):
        self.value: bool = MISSING
        super().__init__(timeout=60)

    @discord.ui.button(emoji='✅', style=discord.ButtonStyle.grey)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await self.disable_all(interaction.message)
        self.stop()

    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.grey)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await self.disable_all(interaction.message)
        self.stop()


class WebhookGroup(app_commands.Group):
    def __init__(self, cog: Webhooks):
        self.cog = cog
        super().__init__(name='webhook', description='A group command to make your own webhook!')

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild:
            return True
        raise NoPrivateMessage('Try this in a server.')

    @app_commands.command(description='Create a webhook user.')
    async def create(self, interaction: discord.Interaction, name: str, avatar: str = None):
        if self.cog.users.get(interaction.user.id):
            view = ConfirmView()
            await interaction.response.send_message('Are you sure you would like to replace your old webhook users?',
                                                    view=view)
            await view.wait()
            if view.value is True:
                pass
            elif view.value is False:
                await interaction.followup.send('Cancelling.')
                return
            else:
                await interaction.followup.send('You did not click a button in time.')
                return

        if name.lower() == 'clyde':
            await smart_send(interaction, f'The name cannot be `{name}`')
            return

        embed = discord.Embed(title='New Webhook User!')
        embed.add_field(name='Name', value=name)

        if avatar is not None:
            if not avatar.startswith('http://') and not avatar.startswith('https://'):
                await smart_send(interaction, 'Avatar must be a url starting with `http://` or `https://`')
                return
            embed.set_thumbnail(url=avatar)

        self.cog.users[interaction.user.id] = {'name': name, 'avatar': avatar}
        await smart_send(interaction, embed=embed)

    @app_commands.command(description='Send a message with your webhook.')
    async def send(self, interaction: discord.Interaction, content: str):
        data = self.cog.users.get(interaction.user.id)
        if data is None:
            embed = discord.Embed(title="You don't have a user",
                                  description=f'Use `/webhook create` to create one')
            await interaction.response.send_message(embed=embed)
            return

        try:
            webhook = self.cog.webhooks[interaction.channel.id]
        except KeyError:
            webhook = await interaction.channel.create_webhook(name='MasterBotWebhook')
            self.cog.webhooks[interaction.channel.id] = webhook

        await webhook.send(content=content,
                           username=data['name'],
                           avatar_url=data['avatar'])
        await interaction.response.send_message(f'Sending message:\n{content}', ephemeral=True)


class Webhooks(Cog, name='webhooks'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.session = None
        self.webhooks: dict[int, discord.Webhook] = {}
        self.users: dict[int, dict[str, str | None]] = {}
        self.db = None
        print('Webhook cog loaded')

    async def cog_load(self):
        await super().cog_load()
        self.session = aiohttp.ClientSession(loop=self.bot.loop)
        self.update_db.start()
        self.bot.tree.add_command(WebhookGroup(self))

    async def cog_unload(self):
        await super().cog_unload()
        await self.session.close()
        self.update_db.cancel()
        self.bot.tree.remove_command('webhook')

    async def cog_command_error(self, ctx, error):
        error: commands.CommandError

        if ctx.command is None:
            return
        if isinstance(error, commands.BotMissingPermissions):
            if 'manage_webhooks' in error.missing_permissions:
                embed = discord.Embed(title='I need `manage_webhooks` permissions.',
                                      description='Tell someone to give it to me')
                await ctx.send(embed=embed)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send('Try this in a server.')
        else:
            await self.bot.on_command_error(ctx, error)

    async def fetch_webhooks(self):
        for channel in self.bot.get_all_channels():
            async with self.db.execute(f"""SELECT webhook_id, webhook_token FROM webhooks
                                           WHERE id = {channel.id};""") as cursor:
                data = await cursor.fetchone()
            if data is None:
                continue
            webhook_id, webhook_token = data
            self.webhooks[channel.id] = discord.Webhook.from_url(
                url=f'https://discord.com/api/webhooks/{webhook_id}/{webhook_token}',
                session=self.session,
                bot_token=self.bot.http.token
            )

        users = list(set(self.bot.users))  # to remove dupes
        for user in users:
            cursor = await self.db.execute(f"""SELECT name, avatar FROM users
                                            WHERE id = {user.id}""")
            data = await cursor.fetchone()
            if data is None:
                continue
            name, avatar = data
            if avatar == 'None':
                avatar = None
            self.users[user.id] = {'name': name, 'avatar': avatar}

    @tasks.loop(minutes=7)
    async def update_db(self):
        for k, v in self.webhooks.items():
            try:
                await self.db.execute(f"""INSERT INTO webhooks VALUES ({k},
                {v.id},
                '{v.token}')""")
            except IntegrityError:
                await self.db.execute(f"""UPDATE webhooks
                SET webhook_id = {v.id}, webhook_token = '{v.token}'
                WHERE id = {k};""")
        for k, v in self.users.items():
            try:
                await self.db.execute(f"""INSERT INTO users VALUES ({k},
                '?',
                '?')""", (v['name'], v['avatar']))
            except IntegrityError:
                await self.db.execute(f"""UPDATE users
                SET name = '?', avatar = '?'
                WHERE id = {k};""", (v['name'], v['avatar']))
        await self.db.commit()

    @update_db.before_loop
    async def before(self):
        await self.bot.wait_until_ready()
        self.db = await aiosqlite.connect('cogs/databases/webhooks.db')
        await self.db.execute("""CREATE TABLE IF NOT EXISTS webhooks (
                                        id INTEGER PRIMARY KEY,
                                        webhook_id INT,
                                        webhook_token TEXT
                                    );""")
        await self.db.execute("""CREATE TABLE IF NOT EXISTS users (
                                        id INTEGER PRIMARY KEY,
                                        name TEXT,
                                        avatar TEXT
                                    );""")
        await self.db.commit()
        await self.fetch_webhooks()

    @update_db.after_loop
    async def close_session(self):
        await self.update_db()
        await self.db.close()
        await self.session.close()

    @commands.group(description="Make a 'bot' account.")
    async def webhook(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title='Categories',
                                  description='`create`\n`send`')
            embed.set_footer(text='Use create to modify your webhook.')
            await ctx.send(embed=embed)

    @webhook.command(description='Create your own user. (Kinda)')
    @commands.guild_only()
    @commands.bot_has_permissions(manage_webhooks=True)
    async def create(self, ctx: commands.Context, *, flags: WebhookUserFlags):
        if self.users.get(ctx.author.id):
            msg = await ctx.send('Are you sure you would like to replace your old webhook users?')
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')

            check = lambda r, u: u == ctx.author and r.message == msg and str(r.emoji) in ('✅', '❌')
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            except asyncio.TimeoutError:
                return await ctx.send('Cancelling.')
            else:
                if str(reaction.emoji) == '❌':
                    return await ctx.send('Cancelling.')

        if flags.name.lower() == 'clyde':
            await ctx.send('The name cannot be `clyde`')
            return

        embed = discord.Embed(title='New Webhook User!')
        embed.add_field(name='Name', value=flags.name)

        if flags.avatar is not None:
            if not flags.avatar.startswith('http://') and not flags.avatar.startswith('https://'):
                return await ctx.send('Avatar must be a url starting with `http://` or `https://`')
            embed.set_thumbnail(url=flags.avatar)

        self.users[ctx.author.id] = {'name': flags.name, 'avatar': flags.avatar}

        await ctx.send(embed=embed)
        await ctx.message.delete(delay=3)

    @create.error
    async def error(self, ctx, error):
        if isinstance(error, (commands.MissingRequiredArgument,
                              commands.MissingRequiredFlag,
                              commands.MissingFlagArgument)):
            embed = discord.Embed(title='Missing flag arguments')
            embed.add_field(name='name', value='A name.')
            embed.add_field(name='avatar', value='Optional. A avatar for the URL.')
            embed.set_footer(text=f'Example: {ctx.prefix}create name: XbowMaster avatar: https://someurl.com/')
            await ctx.send(embed=embed)
        else:
            raise error

    @webhook.command(description='Send a message with that.')
    @commands.guild_only()
    @commands.bot_has_permissions(manage_webhooks=True)
    async def send(self, ctx: commands.Context, *, content):
        data = self.users.get(ctx.author.id)
        if data is None:
            embed = discord.Embed(title="You don't have a user",
                                  description=f'Use `{ctx.clean_prefix}webhook create` to create one')
            return await ctx.reply(embed=embed)
        try:
            webhook = self.webhooks[ctx.channel.id]
        except KeyError:
            webhook = await ctx.channel.create_webhook(name='MasterBotWebhook')
            self.webhooks[ctx.channel.id] = webhook
        print(data)
        await webhook.send(content=content,
                           username=data['name'],
                           avatar_url=data['avatar'])
        await ctx.message.delete()

    @send.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply('What do I send?', delete_after=5)
        else:
            raise error

    @webhook.command(description='Delete it.')
    async def delete(self, ctx):
        if not self.users.get(ctx.author.id):
            await ctx.send("You don't even have one...")
            return

        del self.users[ctx.author.id]
        await ctx.send('Done.')


async def setup(bot: MasterBot):
    await Webhooks.setup(bot)
