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
pip install -U git+https://github.com/chawkk6404/MasterBot
```
________
Config
------
Create a json file named `config.json`
Add data with this structure
```json
{
  "token": "bot token",
  "api_keys": {
    "clash_royale": "API key from https://developer.clashroyale.com/#/",
    "weather": ""
  },
  "command_prefix": "!",
  "logger": "logs/discord.log"
}
```

________

Short Example
-------------
```py
import masterbot


bot = masterbot.MasterBot(cogs=masterbot.cog_list)


if __name__ == '__main__':
    bot.run()
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
        super().__init__(bot)
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
                                            
                                            
my_cogs = ['cogs.hello']
my_cogs.extend(masterbot.cog_list)

bot = masterbot.MasterBot(cogs=my_cogs)


if __name__ == '__main__':
    bot.run()
 ```
