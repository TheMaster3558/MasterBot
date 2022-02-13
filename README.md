# MasterBot
The MasterBot discord bot created by The Master#6404


Short Example
-------------
```py
import masterbot


api_keys = masterbot.MasterBotAPIKeyManager(clash_royale='API key from https://developer.clashroyale.com/#/',
                                            weather='API key from https://www.weatherapi.com/')

bot = masterbot.MasterBot(cogs=masterbot.cog_list, api_keys=api_keys)


if __name__ == '__main__':
    bot.run('token')
```
