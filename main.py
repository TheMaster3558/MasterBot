from masterbot import MasterBot, cog_list


bot = MasterBot(cogs=cog_list, log='logs/discord.log')


# two tokens for my two bots
TOKEN1 = 'OTI0MDM1ODc4ODk1MTEyMjUz.YcYteQ.C6CEOvXrumyLiWQoKCPy2XlQ6l0'
TOKEN2 = 'ODc4MDM1MDY3OTc5NTYzMDY5.YR7T4Q.JLoUwmy5OvTo2c9lmisvZMqUaPc'


if __name__ == '__main__':
    bot.run(TOKEN1)
