# MasterBot
The MasterBot discord bot created by The Master#6404
____________


Installation
-------------
You **MUST** install discord.py v2 from GitHub

```
pip install -U git+https://github.com/Rapptz/discord.py
```

Then you can install MasterBot from GitHub
```
https://github.com/chawkk6404/MasterBot
```


________

Short Example
-------------
```py
import masterbot


"""api_keys = masterbot.MasterBotAPIKeyManager(clash_royale='API key from https://developer.clashroyale.com/#/',
                                            weather='API key from https://www.weatherapi.com/')"""

bot = masterbot.MasterBot(cogs=masterbot.cog_list, api_keys=api_keys)


if __name__ == '__main__':
    bot.run('token')
```


Cog Example
-----------
`cogs/hello.py`
```py
import slash_util
import masterbot
import discord
from discord.ext import commands


class Hello(slash_util.Cog):
    def __init__(self, bot: masterbot.MasterBot):
        self.bot = bot
        self.letters = {}
       
    @commands.command()
    async def letter(self, ctx, letter):
        self.letters[ctx.author.id] = letter
    
    @commands.command()
    async def myletter(self, ctx, user: discord.User = None):
        user = user or ctx.author
        letter = self.letters.get(user.id)
        if letter is None:
            return await ctx.send("{0.name} doesn't have a letter saved".format(user))
        await ctx.send("Your letter is {}".format(letter))
    
    @slash_util.slash_command(name='letter')
    async def _letter(self, ctx, letter: str):
        self.letters[ctx.author.id] = letter
    
    @slash_util.slash_command(name='myletter')
    async def _myletter(self, ctx, user: discord.User = None):
        user = user or ctx.author
        letter = self.letters.get(user.id)
        if letter is None:
            return await ctx.send("{0.name} doesn't have a letter saved".format(user))
        await ctx.send("Your letter is {}".format(letter))
    
 def setup(bot: masterbot.MasterBot):
     bot.add_cog(Hello(bot))
 ```
 
 Combining Both Examples
 -----------------------
 ```py
import masterbot
 
 
api_keys = masterbot.MasterBotAPIKeyManager(clash_royale='API key from https://developer.clashroyale.com/#/',
                                            weather='API key from https://www.weatherapi.com/')
                                            
                                            
my_cogs = ['cogs.hello']
my_cogs.extend(masterbot.cog_list)

bot = masterbot.MasterBot(cogs=my_cogs, api_keys=api_keys)


if __name__ == '__main__':
    bot.run('token')
 ```
