import discord


class Embed(discord.Embed):
    """Set the default color to 0x2F3136"""

    def __init__(self, **kwargs):
        if 'color' not in kwargs and 'colour' not in kwargs:
            kwargs['color'] = 0x2F3136

        super().__init__(**kwargs)


discord.Embed = Embed
