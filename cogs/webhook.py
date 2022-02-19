"""
License: Apache License 2.0
2021-present The Master
See LICENSE for more
"""


import discord
from discord.ext import commands, tasks
import aiohttp
from typing import Optional, Dict
import asyncio
import slash_util
from bot import MasterBot
import aiosqlite
from sqlite3 import IntegrityError


class Help:
    def __init__(self, prefix):
        self.prefix = prefix

    def webhook_help(self):
        message = f'`{self.prefix}webhook create <flags>`: Create your own webhook user!\nFlags:\n**name**\n**avatar** (optional. should be url)\n' \
                  f'`{self.prefix}webhook send <message>`: Send a message with the webhook.'
        return message

    def delete_help(self):
        message = f'`{self.prefix}wdelete`: Delete the data of your webhook user.'
        return message

    def full_help(self):
        help_list = [self.webhook_help(), self.delete_help()]
        return '\n'.join(help_list) + '\nNot available with Slash Commands yet'


class WebhookUserFlags(commands.FlagConverter):
    name: str
    avatar: Optional[str] = None


class Webhooks(slash_util.Cog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.session = None
        self.webhooks: Dict[int, discord.Webhook] = {}
        self.users: Dict[int, Dict[str, Optional[str]]] = {}
        self.db = None
        self.update_db.start()
        print('Webhook cog loaded')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.command is None:
            return
        if ctx.command.cog != self:
            return
        if isinstance(error, commands.BotMissingPermissions):
            if 'manage_webhooks' in error.missing_permissions:
                embed = discord.Embed(title='I need `manage_webhooks` permissions.',
                                      description='Tell someone to give it to me')
                await ctx.send(embed=embed)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send('Try this in a server.')
        else:
            raise error

    async def fetch_webhooks(self):
        for channel in self.bot.get_all_channels():
            cursor = await self.db.execute(f"""SELECT webhook_id, webhook_token FROM webhooks
                                           WHERE id = {channel.id};""")
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

    @tasks.loop(minutes=1)
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
                '{v['name']}',
                '{v['avatar']}')""")
            except IntegrityError:
                await self.db.execute(f"""UPDATE users
                SET name = '{v['name']}', avatar = '{v['avatar']}'
                WHERE id = {k};""")
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
        self.session = aiohttp.ClientSession(loop=self.bot.loop)
        await self.fetch_webhooks()

    @update_db.after_loop
    async def close_session(self):
        await asyncio.sleep(1.5)
        await self.update_db()
        await self.session.close()

    @commands.group()
    async def webhook(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title='Categories',
                                  description='`create`\n`send`')
            embed.set_footer(text='Use create to modify your webhook.')

    @webhook.command()
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
            return await ctx.send('The name cannot be `clyde`')
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

    @webhook.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_webhooks=True)
    async def send(self, ctx: commands.Context, *, content):
        data = self.users.get(ctx.author.id)
        if data is None:
            embed = discord.Embed(title="You don't have a user",
                                  description=f'Use `{await self.bot.get_prefix(ctx.message)}create` to create one')
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

    @commands.command()
    async def wdelete(self, ctx):
        if not self.users.get(ctx.author.id):
            return await ctx.send("You don't even have one...")
        del self.users[ctx.author.id]
        await ctx.send('Done.')


def setup(bot: MasterBot):
    bot.add_cog(Webhooks(bot))
