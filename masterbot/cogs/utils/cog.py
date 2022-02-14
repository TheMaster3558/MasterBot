import slash_util


class Cog(slash_util.Cog):
    @classmethod
    def load(cls, bot: slash_util.Bot):
        bot.add_cog(cls(bot))
