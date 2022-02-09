import discord
from typing import Tuple, Any, Union, Optional


class EmbedField:
    def __init__(self, name: str, value: Any, inline: Optional[bool] = False):
        self.name = name
        self.value = value
        self.inline = inline

    def __str__(self):
        return f'{self.name}: {self.value}'

    def __repr__(self):
        return f'name={self.name}, value={self.value}, inline={self.inline}'


class Embed(discord.Embed):
    def add_fields(self, *fields: Union[EmbedField, Tuple[str, Any, Optional[bool]]]):
        for field in fields:
            if isinstance(field, (list, tuple)):
                if len(field) == 2:
                    name, value = field
                    inline = False
                else:
                    name, value, inline = field
                self.add_field(name=name, value=value, inline=inline)
            elif isinstance(field, EmbedField):
                self.add_field(name=field.name, value=field.value, inline=field.inline)

    async def send(self, channel: Union[discord.TextChannel, discord.DMChannel, discord.Thread]):
        await channel.send(embed=self)
