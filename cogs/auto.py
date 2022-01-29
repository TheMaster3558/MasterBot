import discord
from discord.ext import commands, tasks
import re
import slash_util
from motor import motor_asyncio
from pymongo.errors import DuplicateKeyError


class Auto(slash_util.ApplicationCog):
    defaults = ['email', 'phone', 'token']
    default_options = {'email': False, 'phone': False, 'token': True}

    def __init__(self, bot):
        super().__init__(bot)
        self.defaults = {
            'email': re.compile('\w+@[a-z]+\.[a-z]{2,3}'),
            'phone': re.compile('\(?\d{3}\)?-\d{3}-\d{4}'),
            'token': re.compile('[A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}')
        }
        self.mongo_client = motor_asyncio.AsyncIOMotorClient(
            'mongodb+srv://chawkk:Xboxone87@masterbotcluster.ezbjl.mongodb.net/test')
        self.db = self.mongo_client['auto']['options']
        self.options = {}
        self.custom = {}
        self.log = self.bot.cogs.get('Moderation').log
        self.update_mongo.start()
        print('Auto cog loaded')

    async def fetch_data(self):
        for guild in self.bot.guilds:
            data = await self.db.find_one({'_id': str(guild.id)})
            if data:
                del data['_id']
                self.options[str(guild.id)] = data.get('options')
                remains = set(self.default_options) - set(self.options[str(guild.id)])
                for option in remains:
                    self.options[str(guild.id)][option] = self.default_options.get(option)
            else:
                self.options[str(guild.id)] = self.default_options

    @tasks.loop(seconds=10)
    async def update_mongo(self):
        print(self.options)
        for k, v in self.options.items():
            payload = {'_id': k, 'options': v}
            try:
                await self.db.insert_one(payload)
            except DuplicateKeyError:
                await self.db.update_one({'_id': k}, {'$set': {'options': v}})

    @update_mongo.before_loop
    async def wait(self):
        await self.bot.wait_until_ready()
        await self.fetch_data()

    @update_mongo.after_loop
    async def final(self):
        await self.update_mongo()

    @commands.group()
    async def auto(self, ctx):
        pass

    @auto.command()
    async def disable(self, ctx, *options):
        if len(options) == 0:
            return await ctx.send('Give something.')
        for option in options:
            if option in self.defaults:
                self.options[str(ctx.guild.id)][option] = False
        await ctx.send(f'The following have been disabled: {", ".join(options)}')

    @auto.command()
    async def enable(self, ctx, *options):
        if len(options) == 0:
            return await ctx.send('Give something.')
        for option in options:
            if option in self.defaults:
                self.options[str(ctx.guild.id)][option] = True
        await ctx.send(f'The following have been enabled: {", ".join(options)}')
        print(self.options)

    @commands.Cog.listener('on_message')
    async def delete_message(self, message: discord.Message):
        result = None
        skip = [k for k, v in self.options[str(message.guild.id)].items() if v is False]
        for k, v in self.defaults.items():
            if k in skip:
                continue
            if v.search(message.content):
                await message.delete()
                result = k
        if result is None:
            return
        log = await self.log.find_one({'_id': str(message.guild.id)})
        if log:
            channel = self.bot.get_channel(int(log.get('channel')))
            embed = discord.Embed(title='Message deleted',
                                  timestamp=message.created_at)
            embed.add_field(name='Author', value=message.author.mention)
            embed.add_field(name='Reason', value=f'Possible {result}')
            embed.add_field(name='Content', value=message.content)
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Auto(bot))
