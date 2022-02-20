# MasterBot
A Discord Bot created by The Master

-------
Running
-----
If you choose to run the bot yourself which is not recommended, follow these steps

**1. Install Python 3.10 or higher**\
**2. Install requirements from `requirements.txt`**\
**3. Create a directory named `databases`**\
    Sqlite Databases will be stored here\
**4. import MasterBot into `main.py`**\
**5. Add your Weather and Clash Royale API keys**\
[Clash Royale](https://developer.clashroyale.com/#/) \
[Weather](https://www.weatherapi.com/) \
**6. Create a MongoDB cluster. Within in create a database `moderation` then a collection `channel`**\
**7. Run your bot with your token**
```py
from bot import MasterBot

bot = MasterBot("Clash Royale API key first",
                "Weather API key second",
                "Your MongoDB key here third")

if __name__ == '__main__':
    bot.run('your token here')
```
