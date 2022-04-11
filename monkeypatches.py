import discord


class Embed(discord.Embed):
    """Set the default color to 0x2F3136"""

    def __init__(self, **kwargs):
        if not kwargs.get('color') and kwargs.get('colour'):
            kwargs['color'] = 0x2F3136

        super().__init__(**kwargs)


discord.Embed = Embed
