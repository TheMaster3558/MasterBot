import discord
from discord.ext import commands, tasks
import re
import slash_util
from motor import motor_asyncio
from pymongo.errors import DuplicateKeyError
import codecs


class Help:
    def __init__(self, prefix):
        self.prefix = prefix

    def auto_help(self):
        message = (
            f"`{self.prefix}auto enable <options>`: Turn on and off some of the builtin delete regex. They are email, phone, and token. All are disabled by default but token\n"
            f"`{self.prefix}auto disable <options>`: Disable some of the default delete regex\n"
        )
        return message

    def custom_help(self):
        message = (
            f"`{self.prefix}custom <name> <regex>`: Create a new regex to delete. Name it to identify\n"
            f"`{self.prefix}cdelete <name>`: Delete one of the customs with the name"
        )
        return message

    def full_help(self):
        help_list = [self.auto_help(), self.custom_help()]
        return "\n".join(help_list)


class Auto(slash_util.ApplicationCog):
    default_names = ["email", "phone", "token"]
    default_options = {"email": False, "phone": False, "token": True}

    def __init__(self, bot):
        super().__init__(bot)
        self.defaults = {
            "email": re.compile("\w+@[a-z]+\.[a-z]{2,3}"),
            "phone": re.compile("\(?\d{3}\)?-\d{3}-\d{4}"),
            "token": re.compile("[A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}"),
        }
        print("Connected to mongodb... (Auto cog)")
        self.mongo_client = motor_asyncio.AsyncIOMotorClient(
            "mongodb+srv://chawkk:Xboxone87@masterbotcluster.ezbjl.mongodb.net/test"
        )
        self.db = self.mongo_client["auto"]["options"]
        self.log = self.bot.cogs.get("Moderation").log
        print("Connected.")
        self.update_mongo.start()
        self.options = {}
        self.custom = {}
        print("Auto cog loaded")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if str(guild.id) not in self.options:
            self.options[str(guild.id)] = self.default_options

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if str(guild.id) in self.options:
            del self.options[str(guild.id)]

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if ctx.command is None:
            return
        if ctx.command.cog != self:
            return
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            if not ctx.command.has_error_handler():
                raise error

    async def fetch_data(self):
        for guild in self.bot.guilds:
            data = await self.db.find_one({"_id": str(guild.id)})
            if data:
                del data["_id"]
                self.options[str(guild.id)] = data.get("options")
                remains = set(self.default_options) - set(self.options[str(guild.id)])
                for option in remains:
                    self.options[str(guild.id)][option] = self.default_options.get(
                        option
                    )
            else:
                self.options[str(guild.id)] = self.default_options
            self.custom[str(guild.id)] = {}

    @tasks.loop(seconds=10)
    async def update_mongo(self):
        for k, v in self.options.items():
            payload = {"_id": k, "options": v}
            try:
                await self.db.insert_one(payload)
            except DuplicateKeyError:
                await self.db.update_one({"_id": k}, {"$set": {"options": v}})

    @update_mongo.before_loop
    async def wait(self):
        await self.bot.wait_until_ready()
        await self.fetch_data()

    @update_mongo.after_loop
    async def final(self):
        await self.update_mongo()

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def auto(self, ctx):
        await ctx.send("`auto` categories are `disable` and `enable` and `custom`")

    @auto.command()
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx, *options):
        if len(options) == 0:
            return await ctx.send("Give something.")
        for option in options:
            if option in self.default_names:
                self.options[str(ctx.guild.id)][option] = False
        await ctx.send(f'The following have been disabled: {", ".join(options)}')

    @auto.command()
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx, *options):
        if len(options) == 0:
            return await ctx.send("Give something.")
        for option in options:
            if option in self.default_names:
                self.options[str(ctx.guild.id)][option] = True
        await ctx.send(f'The following have been enabled: {", ".join(options)}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def custom(self, ctx, name, *, regex):
        if name in self.default_names:
            return await ctx.send("You can't use that name.")
        regex = codecs.decode(regex, "unicode_escape")
        self.custom[str(ctx.guild.id)][name] = regex

    @custom.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if ctx.prefix == "!":
                prefix = "!"
            else:
                prefix = f"@{self.bot.name}"
            await ctx.send(f"Bad format. `{prefix}custom <name> <regex>`")
        else:
            raise error

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def cdelete(self, ctx, *, name):
        guild_options = self.custom[str(ctx.guild.id)]
        if name not in guild_options:
            await ctx.send(f'Customs are {", ".join(guild_options.keys())} not {name}')
        del guild_options[name]
        await self.db.delete_many()
        await ctx.send("Ok. Done.")

    @cdelete.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if ctx.prefix == "!":
                prefix = "!"
            else:
                prefix = f"@{self.bot.name}"
            await ctx.send(f"Bad format. `{prefix}delete <name>`")
        else:
            raise error

    async def check_delete(self, message: discord.Message):
        if (
            message.channel.permissions_for(message.guild.me).manage_messages
            and message.author.top_role.position <= message.guild.me.top_role.position
        ):
            await message.delete()

    async def search_message(self, message: discord.Message):
        content = message.content
        skip = [k for k, v in self.options[str(message.guild.id)].items() if v is False]
        for k, v in self.defaults.items():
            if k in skip:
                continue
            if v.search(content):
                await self.check_delete(message)
                return k
        guild_extras = self.custom[str(message.guild.id)]
        for k, v in guild_extras.items():
            if re.search(v, content):
                await self.check_delete(message)
                return k
        return None

    @commands.Cog.listener("on_message")
    async def delete_message(self, message: discord.Message):
        if not isinstance(message.author, discord.Member):
            return
        if not message.guild:
            return
        if "custom" in message.content:
            return
        if message.author.top_role.position >= message.guild.me.top_role.position:
            return
        if message.author.guild_permissions.administrator:
            return
        result = await self.search_message(message)
        if result is None:
            return
        log = await self.log.find_one({"_id": str(message.guild.id)})
        if log:
            channel = self.bot.get_channel(int(log.get("channel")))
            embed = discord.Embed(
                title="Suspicious message", timestamp=message.created_at
            )
            embed.add_field(name="Author", value=message.author.mention)
            embed.add_field(name="Reason", value=f"Possible {result}")
            embed.add_field(name="Content", value=message.content)
            embed.set_footer(text="Message may have been deleted by me")
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Auto(bot))
