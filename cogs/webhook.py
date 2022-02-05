import discord
from discord.ext import commands, tasks
import aiohttp
from motor import motor_asyncio
from pymongo.errors import DuplicateKeyError
from typing import Optional
import asyncio
from bot import MasterBot


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
        return '\n'.join(help_list)


class WebhookUserFlags(commands.FlagConverter):
    name: str
    avatar: Optional[str] = None


class Webhooks(commands.Cog):
    def __init__(self, bot: MasterBot):
        self.bot = bot
        self.session = None
        print('Connecting to mongodb... (Webhooks cog)')
        self.client = motor_asyncio.AsyncIOMotorClient(
            'mongodb+srv://chawkk:Xboxone87@masterbotcluster.ezbjl.mongodb.net/test')
        self.channel_db = self.client['webhook']['channels']
        self.user_db = self.client['webhook']['users']
        print('Connected.')
        self.webhooks = {}
        self.users = {}
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
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send('Try this in a server.')

    async def fetch_webhooks(self):
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.permissions_for(guild.me).manage_webhooks:
                    webhook = await self.channel_db.find_one({'_id': str(channel.id)})
                    if webhook is not None:
                        self.webhooks[channel.id] = discord.Webhook.from_url(
                            f'https://discord.com/api/webhooks/{webhook.get("webhook_id")}/{webhook.get("webhook_token")}',
                            session=self.session,
                            bot_token=self.bot.http.token
                        )
            data = await self.user_db.find_one({'_id': str(guild.id)})
            self.users[guild.id] = {}
            if not data:
                continue
            for k, v in data.get('users').items():
                self.users[guild.id][k] = v

    @tasks.loop(minutes=1)
    async def update_db(self):
        for k, v in self.webhooks.items():
            payload = {'_id': str(k), 'webhook_id': str(v.id), 'webhook_token': v.token}
            try:
                await self.channel_db.insert_one(payload)
            except DuplicateKeyError:
                await self.channel_db.update_one({'_id': str(k)}, {'$set': payload})
        for k, v in self.users.items():
            payload = {'_id': str(k), 'users': v}
            try:
                await self.user_db.insert_one(payload)
            except DuplicateKeyError:
                await self.user_db.update_one({'_id': str(k)}, {'$set': {'users': v}})

    @update_db.before_loop
    async def before(self):
        await self.bot.wait_until_ready()
        self.session = aiohttp.ClientSession()
        await self.fetch_webhooks()
        print('Webhooks fetched (Webhook cog)')

    @update_db.after_loop
    async def close_session(self):
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
        if self.users[ctx.guild.id].get(str(ctx.author.id)):
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
        self.users[ctx.guild.id][str(ctx.author.id)] = {'name': flags.name, 'avatar': flags.avatar}
        embed = discord.Embed(title='New Webhook User!')
        embed.add_field(name='Name', value=flags.name)
        if flags.avatar is not None:
            if not flags.avatar.startswith('http://') and not flags.avatar.startswith('https://'):
                return await ctx.send('Avatar must be a url starting with `http://` or `https://`')
            embed.set_thumbnail(url=flags.avatar)
        await ctx.send(embed=embed)
        await ctx.message.delete(delay=3)

    @webhook.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_webhooks=True)
    async def send(self, ctx: commands.Context, *, content):
        data = self.users[ctx.guild.id].get(str(ctx.author.id))
        if data is None:
            embed = discord.Embed(title="You don't have a user",
                                  description=f'Use `{self.bot.get_prefix(ctx.message)}create` to create one')
            return await ctx.reply(embed=embed)
        try:
            webhook = self.webhooks[ctx.channel.id]
        except KeyError:
            webhook = await ctx.channel.create_webhook(name='MasterBotWebhook')
            self.webhooks[ctx.channel.id] = webhook
        await webhook.send(content=content,
                           username=data['name'],
                           avatar_url=data['avatar'])
        await ctx.message.delete()

    @commands.command()
    @commands.guild_only()
    async def wdelete(self, ctx):
        if not self.users[ctx.guild.id].get(str(ctx.author.id)):
            return await ctx.send("You don't even have one...")
        del self.users[ctx.guild.id][str(ctx.author.id)]
        await ctx.send('Done.')


def setup(bot: MasterBot):
    bot.add_cog(Webhooks(bot))





